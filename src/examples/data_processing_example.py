"""
展示如何使用数据处理模块的示例文件
"""

import asyncio
import logging
from datetime import datetime
import os

from biologic import connect
from biologic.techniques.ocv import OCVTechnique, OCVParams
from biologic.techniques.cv import CVTechnique, CVParams, CVStep
from biologic.techniques.peis import PEISTechnique, PEISParams, SweepMode

from src.utils.data_processing import (
    create_experiment_config,
    ExperimentController
)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def run_example():
    # 创建实验配置
    strDate = datetime.now().strftime("%Y%m%d")
    strRunNumber = "001"
    strExperimentID = f"{strDate}_{strRunNumber}"
    strExperimentPath = os.path.join(os.getcwd(), 'data', strExperimentID)
    
    # 创建实验配置
    config = create_experiment_config(strExperimentID, strExperimentPath)
    
    # 创建实验控制器
    controller = ExperimentController(config)
    
    # 创建测试技术
    # OCV测试
    ocv_params = OCVParams(
        rest_time_T=10,
        record_every_dT=0.1,
        record_every_dE=0.01
    )
    ocv_tech = OCVTechnique(ocv_params)
    
    # CV测试
    cv_steps = [
        CVStep(voltage=0, scan_rate=0.05, vs_initial=False),
        CVStep(voltage=1, scan_rate=0.05, vs_initial=False),
        CVStep(voltage=0, scan_rate=0.05, vs_initial=False)
    ]
    cv_params = CVParams(
        steps=cv_steps,
        n_cycles=3,
        record_every_dE=0.001
    )
    cv_tech = CVTechnique(cv_params)
    
    # PEIS测试
    peis_params = PEISParams(
        vs_initial=False,
        initial_voltage_step=0.0,
        final_frequency=0.1,
        initial_frequency=100000,
        sweep=SweepMode.Logarithmic,
        amplitude_voltage=0.01,
        frequency_number=50
    )
    peis_tech = PEISTechnique(peis_params)
    
    # 组合所有技术
    techniques = [ocv_tech, cv_tech, peis_tech]
    
    try:
        # 连接设备并运行实验
        with connect('USB0') as bl:
            channel = bl.get_channel(1)
            
            # 初始化控制器
            controller.initialize(channel)
            
            # 运行实验
            await controller.run_experiment(techniques)
            
    except Exception as e:
        logging.error(f"实验失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 运行示例
    asyncio.run(run_example()) 
