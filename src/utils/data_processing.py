"""
数据处理模块，用于处理电化学实验数据的采集、处理、存储和可视化。
包含实时数据处理和显示功能。
"""

import os
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import json

@dataclass
class ExperimentConfig:
    """实验配置数据类"""
    experiment_id: str
    base_path: str
    deposition_path: str
    characterization_path: str

class DataHandler:
    """数据处理器抽象基类"""
    async def handle_data(self, data: Any) -> None:
        pass

class DataAcquisitionModule:
    """数据采集模块"""
    def __init__(self, channel, experiment_config: ExperimentConfig):
        self.channel = channel
        self.config = experiment_config
        self.data_handlers: List[DataHandler] = []
        self.logger = logging.getLogger(__name__)

    def add_handler(self, handler: DataHandler) -> None:
        """添加数据处理器"""
        self.data_handlers.append(handler)

    async def notify_handlers(self, data: Any) -> None:
        """通知所有处理器"""
        for handler in self.data_handlers:
            try:
                await handler.handle_data(data)
            except Exception as e:
                self.logger.error(f"Handler {handler.__class__.__name__} failed: {str(e)}")

    async def start_acquisition(self, techniques: List[Any]):
        """开始数据采集"""
        try:
            runner = self.channel.run_techniques(techniques)
            async for data in runner:
                await self.notify_handlers(data)
                yield data
        except Exception as e:
            self.logger.error(f"Data acquisition failed: {str(e)}")
            raise

class DataProcessor(DataHandler):
    """数据处理模块"""
    def __init__(self):
        self.current_technique = None
        self.tech_index = 0
        self.tech_add = 0
        self.current_df = pd.DataFrame()
        self.logger = logging.getLogger(__name__)

    async def handle_data(self, data: Any) -> pd.DataFrame:
        """处理数据并返回DataFrame"""
        try:
            if hasattr(data.data, 'process_data'):
                return self._process_indexed_data(data)
            return self._process_regular_data(data)
        except Exception as e:
            self.logger.error(f"Data processing failed: {str(e)}")
            raise

    def _process_indexed_data(self, data: Any) -> pd.DataFrame:
        """处理带索引的数据"""
        return pd.DataFrame(data.data.process_data.to_json(), index=[0])

    def _process_regular_data(self, data: Any) -> pd.DataFrame:
        """处理常规数据"""
        return pd.DataFrame(data.data.to_json(), index=[0])

    def get_technique_name(self, data: Any) -> str:
        """获取技术名称"""
        return str(type(data.data)).split("'")[1].split(".")[-2]

class DataStorage(DataHandler):
    """数据存储模块"""
    def __init__(self, experiment_config: ExperimentConfig):
        self.config = experiment_config
        self.logger = logging.getLogger(__name__)

    async def handle_data(self, data: Any) -> None:
        """处理并存储数据"""
        try:
            processor = DataProcessor()
            processed_data = await processor.handle_data(data)
            self.save_data(processed_data, data.tech_index, self.get_technique_type(data))
        except Exception as e:
            self.logger.error(f"Data storage failed: {str(e)}")
            raise

    def save_data(self, data: pd.DataFrame, technique_id: int, technique_name: str) -> None:
        """保存数据到文件"""
        filename = f'{self.config.experiment_id}_{technique_id}_{technique_name}.csv'
        filepath = os.path.join(self.config.characterization_path, filename)
        data.to_csv(filepath, index=False)
        self.logger.info(f"Saved data to {filepath}")

    def load_data(self, technique_id: int, technique_name: str) -> pd.DataFrame:
        """从文件加载数据"""
        filename = f'{self.config.experiment_id}_{technique_id}_{technique_name}.csv'
        filepath = os.path.join(self.config.characterization_path, filename)
        return pd.read_csv(filepath)

    @staticmethod
    def get_technique_type(data: Any) -> str:
        """获取技术类型"""
        return str(type(data.data)).split("'")[1].split(".")[-2]

class RealTimeVisualizer(DataHandler):
    """实时可视化模块"""
    def __init__(self):
        # 设置后端
        import matplotlib
        matplotlib.use('TkAgg')
        
        plt.ion()  # 启用交互模式
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        
        # 初始化数据存储
        self.data_cache = {}
        self.lines = {}
        self.technique_plots = {
            'CV': self._setup_cv_plot,
            'PEIS': self._setup_eis_plot,
            'OCV': self._setup_ocv_plot,
            'CP': self._setup_cp_plot,
            'LP': self._setup_lp_plot,
            'MockOCVTechnique': self._setup_ocv_plot,
            'MockCPTechnique': self._setup_cp_plot,
            'MockPEISTechnique': self._setup_eis_plot,
            'MockCVTechnique': self._setup_cv_plot,
            'MockResult': self._setup_ocv_plot
        }
        
        # 配置图表窗口
        self.figure.canvas.manager.set_window_title('实时电化学数据')
        self.current_technique = None
        
        # 显示图表
        plt.show(block=False)
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("RealTimeVisualizer 初始化完成")

    async def handle_data(self, data: Any) -> None:
        """处理并可视化数据"""
        try:
            # 获取技术类型
            technique_type = self.get_technique_type(data)
            self.logger.debug(f"检测到技术类型: {technique_type}")
            
            # 提取数据
            if hasattr(data, 'data') and hasattr(data.data, 'to_json'):
                json_data = data.data.to_json()
                self.logger.debug(f"接收到数据: {json_data}")
                
                # 如果是新的技术类型，初始化图表
                if technique_type != self.current_technique:
                    self.initialize_plot(technique_type)
                    self.current_technique = technique_type
                    self.data_cache[technique_type] = {'x': [], 'y': []}
                    self.lines[technique_type], = self.ax.plot([], [], 'bo-', markersize=4, label=technique_type)
                    self.ax.legend()
                
                # 获取最新数据点
                x_data, y_data = self._get_plot_data(json_data, technique_type)
                if x_data and y_data:
                    # 添加到数据缓存
                    self.data_cache[technique_type]['x'].extend(x_data)
                    self.data_cache[technique_type]['y'].extend(y_data)
                    
                    # 更新图表
                    self.lines[technique_type].set_data(
                        self.data_cache[technique_type]['x'],
                        self.data_cache[technique_type]['y']
                    )
                    
                    # 调整坐标轴范围
                    self.ax.relim()
                    self.ax.autoscale_view()
                    
                    # 强制重绘
                    self.figure.canvas.draw()
                    self.figure.canvas.flush_events()
                    
                    self.logger.debug(f"更新图表: x={x_data[-1]:.2f}, y={y_data[-1]:.4f}")
                
        except Exception as e:
            self.logger.error(f"可视化错误: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def initialize_plot(self, technique_type: str) -> None:
        """初始化图表"""
        self.logger.info(f"初始化图表: {technique_type}")
        
        # 清除现有图表
        self.ax.clear()
        
        # 根据技术类型设置图表
        if technique_type in self.technique_plots:
            self.technique_plots[technique_type]()
        else:
            self._setup_default_plot()
        
        # 通用设置
        self.ax.grid(True)
        self.figure.tight_layout()
        
        # 强制重绘
        self.figure.canvas.draw()
        plt.pause(0.1)

    def _setup_default_plot(self) -> None:
        """默认图表设置"""
        self.ax.set_xlabel('数据 X')
        self.ax.set_ylabel('数据 Y')
        self.ax.set_title('电化学数据')

    def _setup_cv_plot(self) -> None:
        """设置CV图表"""
        self.ax.set_xlabel('电位 (V)')
        self.ax.set_ylabel('电流 (A)')
        self.ax.set_title('循环伏安法')

    def _setup_eis_plot(self) -> None:
        """设置EIS图表"""
        self.ax.set_xlabel('Re(Z) (Ω)')
        self.ax.set_ylabel('-Im(Z) (Ω)')
        self.ax.set_title('电化学阻抗谱')

    def _setup_ocv_plot(self) -> None:
        """设置OCV图表"""
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('电位 (V)')
        self.ax.set_title('开路电压')

    def _setup_cp_plot(self) -> None:
        """设置CP图表"""
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('电位 (V)')
        self.ax.set_title('恒电流法')

    def _setup_lp_plot(self) -> None:
        """设置LP图表"""
        self.ax.set_xlabel('电位 (V)')
        self.ax.set_ylabel('电流 (A)')
        self.ax.set_title('线性极化')

    def _get_plot_data(self, data: Dict[str, Any], technique_type: str) -> Tuple[List[float], List[float]]:
        """获取绘图数据"""
        if not data:
            return [], []
            
        # 确保所有数据都是列表格式
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                processed_data[key] = [value]
            elif isinstance(value, list):
                processed_data[key] = value
            else:
                try:
                    processed_data[key] = list(value)
                except:
                    processed_data[key] = [value]
        
        # 根据技术类型提取数据
        if technique_type in ['CV', 'MockCVTechnique']:
            return processed_data.get('Ewe', []), processed_data.get('I', [])
        elif technique_type in ['PEIS', 'MockPEISTechnique']:
            re_z = processed_data.get('Re(Z)', [])
            im_z = [-im for im in processed_data.get('Im(Z)', [])] if 'Im(Z)' in processed_data else []
            return re_z, im_z
        elif technique_type in ['OCV', 'CP', 'MockOCVTechnique', 'MockCPTechnique', 'MockResult']:
            return processed_data.get('time', []), processed_data.get('Ewe', [])
        elif technique_type == 'LP':
            return processed_data.get('Ewe', []), processed_data.get('I', [])
        else:
            # 尝试找到任何可以绘图的数值数组
            for key1 in processed_data:
                if isinstance(processed_data[key1], list) and processed_data[key1]:
                    for key2 in processed_data:
                        if key1 != key2 and isinstance(processed_data[key2], list) and processed_data[key2]:
                            self.logger.info(f"使用通用数据: x={key1}, y={key2}")
                            return processed_data[key1], processed_data[key2]
            return [], []

    @staticmethod
    def get_technique_type(data: Any) -> str:
        """获取技术类型"""
        if hasattr(data, 'data'):
            data_obj = data.data
            
            # 方法1：获取类名
            class_name = data_obj.__class__.__name__
            if class_name != 'object':
                return class_name
            
            # 方法2：查找类型属性
            if hasattr(data_obj, 'type'):
                return data_obj.type
            
            # 方法3：查找技术类型属性
            if hasattr(data_obj, 'technique_type'):
                return data_obj.technique_type
        
        return "Unknown"

    def __del__(self):
        """清理资源"""
        try:
            plt.close(self.figure)
            plt.close('all')
        except:
            pass

class ExperimentController:
    """实验控制器"""
    def __init__(self, experiment_config: ExperimentConfig):
        self.config = experiment_config
        self.data_acquisition = None
        self.data_processor = DataProcessor()
        self.data_storage = DataStorage(experiment_config)
        self.visualizer = RealTimeVisualizer()
        self.logger = logging.getLogger(__name__)
        
        # 设置更详细的日志级别
        self.logger.setLevel(logging.DEBUG)
        # 添加控制台处理器
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def initialize(self, channel) -> None:
        """初始化控制器"""
        self.logger.info("初始化实验控制器")
        self.data_acquisition = DataAcquisitionModule(channel, self.config)
        
        # 直接处理数据，而不是通过处理器
        self.data_acquisition.add_handler(self.visualizer)
        self.data_acquisition.add_handler(self.data_storage)
        
        self.logger.info("已添加数据处理器")

    async def run_experiment(self, techniques: List[Any]) -> None:
        """运行实验"""
        try:
            self.logger.info(f"开始实验 {self.config.experiment_id}")
            self.logger.debug(f"技术列表: {[t.__class__.__name__ for t in techniques]}")
            
            async for data in self.data_acquisition.start_acquisition(techniques):
                # 记录每个数据点
                if hasattr(data, 'data') and hasattr(data.data, 'to_json'):
                    json_data = data.data.to_json()
                    self.logger.debug(f"接收到数据点: {json_data}")
                    
                    # 确保数据被正确处理
                    technique_type = (data.data.__class__.__name__ 
                                   if hasattr(data.data, '__class__') 
                                   else "Unknown")
                    self.logger.debug(f"技术类型: {technique_type}")
                    
                    # 检查数据缓存
                    if hasattr(self.visualizer, 'data_cache'):
                        cache_info = {k: len(v['x']) for k, v in self.visualizer.data_cache.items()}
                        self.logger.debug(f"可视化器缓存状态: {cache_info}")
            
            self.logger.info(f"实验 {self.config.experiment_id} 完成")
        except Exception as e:
            self.logger.error(f"实验失败: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise

def create_experiment_config(experiment_id: str, base_path: str) -> ExperimentConfig:
    """创建实验配置"""
    deposition_path = os.path.join(base_path, 'deposition')
    characterization_path = os.path.join(base_path, 'characterization')
    
    # 确保目录存在
    os.makedirs(deposition_path, exist_ok=True)
    os.makedirs(characterization_path, exist_ok=True)
    
    return ExperimentConfig(
        experiment_id=experiment_id,
        base_path=base_path,
        deposition_path=deposition_path,
        characterization_path=characterization_path
    ) 

class ExperimentDataManager:
    """实验数据管理器"""
    
    def __init__(self, experiment_id: str, base_dir: str):
        self.experiment_id = experiment_id
        self.base_dir = base_dir
        
    def save_technique_data(self, 
                          data: pd.DataFrame,
                          technique_id: int,
                          technique_name: str,
                          data_type: str = "characterization") -> str:
        """
        保存技术数据到CSV文件
        
        参数
        ----------
        data : pd.DataFrame
            要保存的数据
        technique_id : int
            技术ID
        technique_name : str
            技术名称
        data_type : str
            数据类型（characterization 或 deposition）
            
        返回
        -------
        str
            保存的文件路径
        """
        filename = f"{self.experiment_id}_{technique_id}_{technique_name}.csv"
        save_dir = os.path.join(self.base_dir, data_type)
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        data.to_csv(filepath, index=False)
        return filepath
    
    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        保存实验元数据到JSON文件
        
        参数
        ----------
        metadata : Dict[str, Any]
            要保存的元数据
            
        返回
        -------
        str
            保存的文件路径
        """
        filename = "metadata.json"
        filepath = os.path.join(self.base_dir, filename)
        os.makedirs(self.base_dir, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        return filepath
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """
        更新现有的元数据文件
        
        参数
        ----------
        updates : Dict[str, Any]
            新的元数据值
        """
        filepath = os.path.join(self.base_dir, "metadata.json")
        
        # 读取现有元数据
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # 更新元数据
        metadata.update(updates)
        
        # 保存更新后的元数据
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def load_technique_data(self, 
                          technique_id: int,
                          technique_name: str,
                          data_type: str = "characterization") -> Optional[pd.DataFrame]:
        """
        从CSV文件加载技术数据
        
        参数
        ----------
        technique_id : int
            技术ID
        technique_name : str
            技术名称
        data_type : str
            数据类型（characterization 或 deposition）
            
        返回
        -------
        Optional[pd.DataFrame]
            加载的数据，如果文件不存在则返回None
        """
        filename = f"{self.experiment_id}_{technique_id}_{technique_name}.csv"
        filepath = os.path.join(self.base_dir, data_type, filename)
        
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        return None
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        加载实验元数据
        
        返回
        -------
        Optional[Dict[str, Any]]
            元数据，如果文件不存在则返回None
        """
        filepath = os.path.join(self.base_dir, "metadata.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None 
