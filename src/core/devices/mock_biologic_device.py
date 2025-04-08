"""
模拟的 Biologic 设备接口
"""

import asyncio
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import logging

@dataclass
class MockData:
    """模拟的数据类"""
    time: Optional[float] = None
    Ewe: Optional[float] = None
    I: Optional[float] = None
    freq: Optional[float] = None
    Re_Z: Optional[float] = None
    Im_Z: Optional[float] = None
    technique_type: str = ''
    _data: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    _index: int = 0
    _max_points: int = 100
    _last_update_index: int = -1  # 跟踪上次更新的索引
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    def add_current_values_to_data(self):
        """将当前值添加到累积数据中"""
        # 避免重复添加相同的数据点
        if self._index <= self._last_update_index:
            self.logger.debug(f"跳过重复数据点: index={self._index}")
            return
            
        self._last_update_index = self._index
        
        if self.technique_type == 'MockOCVTechnique':
            if self.time is not None:
                self._data['time'].append(self.time)
            if self.Ewe is not None:
                self._data['Ewe'].append(self.Ewe)
            self.logger.debug(f"添加OCV数据点: time={self.time}, Ewe={self.Ewe}")
        elif self.technique_type == 'MockCPTechnique':
            if self.time is not None:
                self._data['time'].append(self.time)
            if self.Ewe is not None:
                self._data['Ewe'].append(self.Ewe)
            self.logger.debug(f"添加CP数据点: time={self.time}, Ewe={self.Ewe}")
        elif self.technique_type == 'MockPEISTechnique':
            if self.Re_Z is not None:
                self._data['Re(Z)'].append(self.Re_Z)
            if self.Im_Z is not None:
                self._data['Im(Z)'].append(self.Im_Z)
            self.logger.debug(f"添加PEIS数据点: Re_Z={self.Re_Z}, Im_Z={self.Im_Z}")
        elif self.technique_type == 'MockCVTechnique':
            if self.Ewe is not None:
                self._data['Ewe'].append(self.Ewe)
            if self.I is not None:
                self._data['I'].append(self.I)
            self.logger.debug(f"添加CV数据点: Ewe={self.Ewe}, I={self.I}")
        
        self.logger.info(f"数据点 {self._index} 已添加到 {self.technique_type}, 当前数据大小: {self.get_data_size()}")

    def get_data_size(self) -> str:
        """获取当前数据大小信息"""
        sizes = [f"{key}: {len(value)}" for key, value in self._data.items()]
        return ", ".join(sizes)

    def to_json(self) -> Dict[str, List[float]]:
        """返回累积的数据"""
        # 确保当前值已添加到数据中
        self.add_current_values_to_data()
        # 返回累积的数据的副本
        return {k: list(v) for k, v in self._data.items()}

    async def generate_data(self):
        """生成模拟数据"""
        self.logger.info(f"开始生成 {self.technique_type} 数据")
        while self._index < self._max_points:
            if self.technique_type == 'MockOCVTechnique':
                self.time = self._index * 0.1  # 更快的时间步长
                self.Ewe = 0.3 + 0.2 * np.sin(self._index * 0.1)  # 使用正弦波
            elif self.technique_type == 'MockCPTechnique':
                self.time = self._index * 0.1
                self.Ewe = 0.2 * np.sin(self._index * 0.1)
            elif self.technique_type == 'MockPEISTechnique':
                self.Re_Z = 300 + 200 * np.sin(self._index * 0.1)
                self.Im_Z = -175 + 125 * np.sin(self._index * 0.1)
            elif self.technique_type == 'MockCVTechnique':
                self.Ewe = 0.5 * np.sin(self._index * 0.1)
                self.I = 0.001 * np.cos(self._index * 0.1)
            
            self.add_current_values_to_data()
            self._index += 1
            await asyncio.sleep(0.1)  # 减少延迟到 0.1 秒
            yield self

@dataclass
class OCVParams:
    """模拟的OCV参数类"""
    rest_time_T: float = 60
    record_every_dT: float = 0.5
    record_every_dE: float = 10
    E_range: str = 'E_RANGE_2_5V'
    bandwidth: int = 5

@dataclass
class CPParams:
    """模拟的CP参数类"""
    record_every_dT: float = 0.1
    record_every_dE: float = 0.05
    n_cycles: int = 0
    steps: List[Any] = None
    I_range: str = 'I_RANGE_10mA'

@dataclass
class PEISParams:
    """模拟的PEIS参数类"""
    vs_initial: bool = False
    initial_voltage_step: float = 0.0
    duration_step: int = 60
    record_every_dT: float = 0.5
    record_every_dI: float = 0.01
    final_frequency: float = 1
    initial_frequency: float = 200000
    sweep: str = 'log'
    amplitude_voltage: float = 0.01
    frequency_number: int = 60
    average_n_times: int = 2
    correction: bool = False
    wait_for_steady: float = 0.1
    bandwidth: int = 5
    E_range: str = 'E_RANGE_2_5V'

@dataclass
class CVParams:
    """模拟的CV参数类"""
    record_every_dE: float = 0.01
    average_over_dE: bool = False
    n_cycles: int = 5
    begin_measuring_i: float = 0.5
    end_measuring_i: float = 1
    steps: List[Any] = None
    bandwidth: int = 5
    I_range: str = 'I_RANGE_100mA'

@dataclass
class CPStep:
    """模拟的CP步骤类"""
    current: float
    duration: int
    vs_initial: bool = False

@dataclass
class CVStep:
    """模拟的CV步骤类"""
    voltage: float
    scan_rate: float
    vs_initial: bool = False

class MockTechnique:
    """模拟的电化学技术基类"""
    def __init__(self, params: Any):
        self.params = params
        self.tech_index = 0
        self.name = self.__class__.__name__
        
    async def generate_data(self) -> MockData:
        """生成模拟数据"""
        raise NotImplementedError

class MockOCVTechnique(MockTechnique):
    """模拟的OCV技术"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockOCVTechnique')
        async for d in data.generate_data():
            yield d

class MockCPTechnique(MockTechnique):
    """模拟的CP技术"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockCPTechnique')
        async for d in data.generate_data():
            yield d

class MockPEISTechnique(MockTechnique):
    """模拟的PEIS技术"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockPEISTechnique')
        async for d in data.generate_data():
            yield d

class MockCVTechnique(MockTechnique):
    """模拟的CV技术"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockCVTechnique')
        async for d in data.generate_data():
            yield d

class MockChannel:
    """模拟的通道类"""
    def __init__(self):
        self.techniques = []
        self.current_tech_index = 0
        self.data = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)
    
    def run_techniques(self, techniques: List[MockTechnique]) -> Any:
        """运行技术序列"""
        self.techniques = techniques
        return self
    
    async def __aiter__(self):
        """异步迭代器"""
        for i, tech in enumerate(self.techniques):
            tech.tech_index = i
            self.logger.info(f"开始执行技术 {tech.__class__.__name__} (索引: {i})")
            async for data in tech.generate_data():
                yield MockResult(i, data)

    async def start_technique(self, technique):
        """启动技术测试"""
        self.is_running = True
        self.logger.info(f"启动技术 {technique.__class__.__name__}")
        
        mock_data = MockData(technique_type=technique.__class__.__name__)
        self.logger.debug(f"创建新的 MockData 对象，技术类型: {mock_data.technique_type}")
        
        async for data in mock_data.generate_data():
            if not self.is_running:
                self.logger.info("技术执行被中止")
                break
                
            # 确保技术类型正确设置
            data.technique_type = technique.__class__.__name__
            self.logger.debug(f"生成数据点: {data.get_data_size()}")
            
            yield data
            await asyncio.sleep(0.1)
            
        self.logger.info("技术执行完成")
        self.is_running = False

    def stop(self):
        """停止技术测试"""
        self.logger.info("请求停止技术执行")
        self.is_running = False

class MockResult:
    """模拟的结果类"""
    def __init__(self, tech_index: int, data: MockData):
        self.tech_index = tech_index
        self.data = data

class MockBiologic:
    """模拟的Biologic设备类"""
    def __init__(self, port: str = 'USB0'):
        self.port = port
        self.connected = False
    
    def __enter__(self):
        self.connected = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connected = False
    
    def get_channel(self, channel_number: int) -> MockChannel:
        """获取通道"""
        if not self.connected:
            raise RuntimeError("设备未连接")
        return MockChannel()

def connect(port: str = 'USB0') -> MockBiologic:
    """模拟连接函数"""
    return MockBiologic(port) 
