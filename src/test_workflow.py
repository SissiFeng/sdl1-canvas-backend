"""
工作流测试模块，用于验证自动化实验系统的完整工作流程
包括电沉积和表征实验的测试
"""
import os
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
from collections import defaultdict

from core.devices.mock_biologic_device import (
    MockData, MockOCVTechnique, MockCPTechnique, 
    MockPEISTechnique, MockCVTechnique,
    OCVParams, CPParams, PEISParams, CVParams,
    CPStep, CVStep
)
from utils.config_loader import ExperimentParams
from utils.data_processing import ExperimentDataManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """测试配置"""
    experiment_id: str
    base_dir: str = "test_data"
    deposition_current: float = -0.002  # 沉积电流 (A)
    deposition_duration: float = 60     # 沉积时间 (s)
    well_to_test: str = "C5"           # 测试孔位

class MockBiologicDevice:
    """模拟 Biologic 设备"""
    def __init__(self, data_manager: ExperimentDataManager):
        self.data_manager = data_manager
        self.connected = False
        
    def connect(self) -> bool:
        """连接设备"""
        self.connected = True
        logger.info("Connected to mock Biologic device")
        return True
        
    def disconnect(self) -> bool:
        """断开设备"""
        self.connected = False
        logger.info("Disconnected from mock Biologic device")
        return True
        
    async def run_techniques(self, techniques: List[Any], data_type: str = "characterization") -> None:
        """运行电化学技术序列"""
        if not self.connected:
            raise ConnectionError("Not connected to mock Biologic device")
            
        for tech_id, technique in enumerate(techniques):
            logger.info(f"Running technique {tech_id}: {type(technique).__name__}")
            
            # 生成模拟数据
            data_points = defaultdict(list)
            async for point in technique.generate_data():
                # 从 MockData 对象获取数据
                data = point.to_json()
                for key, values in data.items():
                    if values:  # 只添加非空的最新数据点
                        data_points[key].append(values[-1])
            
            # 将数据点转换为 DataFrame
            df = pd.DataFrame(data_points)
            
            # 保存数据
            self.data_manager.save_technique_data(
                data=df,
                technique_id=tech_id,
                technique_name=type(technique).__name__,
                data_type=data_type
            )
            
class WorkflowTester:
    """工作流测试器"""
    def __init__(self, config: TestConfig):
        self.config = config
        self.data_manager = ExperimentDataManager(
            experiment_id=config.experiment_id,
            base_dir=config.base_dir
        )
        self.device = MockBiologicDevice(self.data_manager)
        
    def setup(self) -> None:
        """设置测试环境"""
        # 创建数据目录
        os.makedirs(os.path.join(self.config.base_dir, "deposition"), exist_ok=True)
        os.makedirs(os.path.join(self.config.base_dir, "characterization"), exist_ok=True)
        
        # 保存元数据
        metadata = {
            "date": datetime.now().strftime("%Y%m%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "experimentID": self.config.experiment_id,
            "cell": self.config.well_to_test,
            "status": "testing",
            "type": "workflow_test"
        }
        self.data_manager.save_metadata(metadata)
        
    async def test_deposition_workflow(self) -> None:
        """测试沉积工作流"""
        logger.info("Testing deposition workflow...")
        
        try:
            # 连接设备
            self.device.connect()
            
            # 创建沉积技术序列
            techniques = []
            
            # 添加 OCV 技术
            ocv_params = OCVParams(
                rest_time_T=60,
                record_every_dT=0.5,
                record_every_dE=10
            )
            techniques.append(MockOCVTechnique(ocv_params))
            
            # 添加 CP 技术
            cp_step = CPStep(
                current=self.config.deposition_current,
                duration=self.config.deposition_duration
            )
            cp_params = CPParams(
                record_every_dT=0.1,
                record_every_dE=0.05,
                steps=[cp_step]
            )
            techniques.append(MockCPTechnique(cp_params))
            
            # 添加最终 OCV
            techniques.append(MockOCVTechnique(ocv_params))
            
            # 运行技术序列
            await self.device.run_techniques(techniques, "deposition")
            
            logger.info("Deposition workflow test completed successfully")
            
        except Exception as e:
            logger.error(f"Error in deposition workflow test: {str(e)}")
            raise
            
        finally:
            self.device.disconnect()
            
    async def test_characterization_workflow(self) -> None:
        """测试表征工作流"""
        logger.info("Testing characterization workflow...")
        
        try:
            # 连接设备
            self.device.connect()
            
            # 创建表征技术序列
            techniques = []
            
            # 添加初始 OCV
            ocv_params = OCVParams(
                rest_time_T=10,
                record_every_dT=0.5
            )
            techniques.append(MockOCVTechnique(ocv_params))
            
            # 添加不同扫描速率的 CV
            for scan_rate in [0.02, 0.04, 0.06, 0.08, 0.1]:
                cv_steps = [
                    CVStep(voltage=-0.2, scan_rate=scan_rate, vs_initial=False),
                    CVStep(voltage=1.0, scan_rate=scan_rate, vs_initial=False),
                    CVStep(voltage=-0.2, scan_rate=scan_rate, vs_initial=False)
                ]
                cv_params = CVParams(
                    record_every_dE=0.01,
                    n_cycles=3,
                    steps=cv_steps
                )
                techniques.append(MockCVTechnique(cv_params))
                
            # 添加 PEIS 技术
            peis_params_list = [
                PEISParams(
                    initial_voltage_step=0.0,
                    final_frequency=0.1,
                    initial_frequency=200000,
                    amplitude_voltage=0.01
                ),
                PEISParams(
                    initial_voltage_step=1.0,
                    final_frequency=0.1,
                    initial_frequency=200000,
                    amplitude_voltage=0.01
                )
            ]
            for params in peis_params_list:
                techniques.append(MockPEISTechnique(params))
            
            # 添加活性和稳定性测试
            cv_steps_activity = [
                CVStep(voltage=0.0, scan_rate=0.05, vs_initial=False),
                CVStep(voltage=1.0, scan_rate=0.05, vs_initial=False),
                CVStep(voltage=0.0, scan_rate=0.05, vs_initial=False)
            ]
            cv_params_activity = CVParams(
                record_every_dE=0.01,
                n_cycles=5,
                steps=cv_steps_activity
            )
            techniques.append(MockCVTechnique(cv_params_activity))
            
            cv_steps_stability = [
                CVStep(voltage=0.0, scan_rate=0.1, vs_initial=False),
                CVStep(voltage=1.0, scan_rate=0.1, vs_initial=False),
                CVStep(voltage=0.0, scan_rate=0.1, vs_initial=False)
            ]
            cv_params_stability = CVParams(
                record_every_dE=0.01,
                n_cycles=1000,
                steps=cv_steps_stability
            )
            techniques.append(MockCVTechnique(cv_params_stability))
            
            # 运行技术序列
            await self.device.run_techniques(techniques, "characterization")
            
            logger.info("Characterization workflow test completed successfully")
            
        except Exception as e:
            logger.error(f"Error in characterization workflow test: {str(e)}")
            raise
            
        finally:
            self.device.disconnect()
            
    async def run_all_tests(self) -> None:
        """运行所有测试"""
        try:
            self.setup()
            await self.test_deposition_workflow()
            await self.test_characterization_workflow()
            
            # 更新测试状态
            self.data_manager.update_metadata({
                "status": "completed",
                "completion_time": datetime.now().strftime("%H:%M:%S")
            })
            
            logger.info("All workflow tests completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow tests failed: {str(e)}")
            self.data_manager.update_metadata({
                "status": "failed",
                "error": str(e)
            })
            raise

async def main():
    """主函数"""
    # 创建测试配置
    config = TestConfig(
        experiment_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # 创建工作流测试器
    tester = WorkflowTester(config)
    
    # 运行测试
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
