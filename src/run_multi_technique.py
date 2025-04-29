"""
多技术电化学实验执行脚本

此脚本从YAML配置文件读取实验序列和参数，然后连续执行多种电化学技术，
同时提供实时Web可视化。
"""

import os
import sys
import asyncio
import logging
import argparse
import yaml
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# 导入项目模块
from src.utils.websocket_server import WebSocketServer
from src.utils.websocket_handler import WebSocketDataHandler
from src.utils.data_processing import create_experiment_config, ExperimentController

# 导入Biologic模块
try:
    from biologic import connect
    from biologic.techniques.ocv import OCVTechnique, OCVParams
    from biologic.techniques.peis import PEISTechnique, PEISParams, SweepMode
    from biologic.techniques.cv import CVTechnique, CVParams, CVStep
    from biologic.techniques.cp import CPTechnique, CPParams, CPStep
    from biologic.techniques.lp import LPTechnique, LPParams, LPStep
    USE_MOCK = False
except ImportError:
    from src.core.devices.mock_biologic_device import (
        connect, MockOCVTechnique as OCVTechnique,
        MockPEISTechnique as PEISTechnique,
        MockCVTechnique as CVTechnique,
        MockCPTechnique as CPTechnique,
        OCVParams, PEISParams, CVParams, CPParams,
        CVStep, CPStep
    )
    USE_MOCK = True

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="多技术电化学实验执行脚本")
    
    parser.add_argument("config", help="实验配置文件路径 (YAML格式)")
    parser.add_argument("--mock", action="store_true", help="使用模拟数据而不是真实设备")
    
    return parser.parse_args()

def load_config(config_path):
    """加载YAML配置文件"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"成功加载配置文件: {config_path}")
        return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        raise

def create_technique_from_config(technique_config):
    """根据配置创建技术对象"""
    technique_type = technique_config['technique'].lower()
    
    # 处理简化配置
    if 'params' not in technique_config:
        return create_technique_from_simple_config(technique_config)
    
    params = technique_config['params']
    
    if technique_type == "ocv":
        ocv_params = OCVParams(
            rest_time=params.get('rest_time', 60),
            record_every_dt=params.get('record_every_dt', 0.1)
        )
        return OCVTechnique(ocv_params)
    
    elif technique_type == "cv":
        cv_steps = [
            CVStep(
                vs_initial=False,
                voltage_step=params.get('voltage_step', 0.5),
                scan_rate=params.get('scan_rate', 0.05),
                n_cycles=params.get('n_cycles', 1)
            )
        ]
        cv_params = CVParams(
            steps=cv_steps,
            n_cycles=params.get('n_cycles', 3),
            record_every_dE=params.get('record_every_dE', 0.001)
        )
        return CVTechnique(cv_params)
    
    elif technique_type == "peis":
        sweep_mode = SweepMode.Logarithmic
        if 'sweep' in params and params['sweep'].lower() == 'linear':
            sweep_mode = SweepMode.Linear
            
        peis_params = PEISParams(
            vs_initial=False,
            initial_voltage_step=params.get('initial_voltage_step', 0.0),
            final_frequency=params.get('final_frequency', 0.1),
            initial_frequency=params.get('initial_frequency', 100000),
            sweep=sweep_mode,
            amplitude_voltage=params.get('amplitude_voltage', 0.01),
            frequency_number=params.get('frequency_number', 50)
        )
        return PEISTechnique(peis_params)
    
    elif technique_type == "cp":
        cp_steps = [
            CPStep(
                current=params.get('current', 0.001),
                duration=params.get('duration', 30),
                vs_initial=False
            )
        ]
        cp_params = CPParams(
            steps=cp_steps,
            record_every_dt=params.get('record_every_dt', 0.1)
        )
        return CPTechnique(cp_params)
    
    elif technique_type == "lp":
        lp_steps = [
            LPStep(
                vs_initial=True,
                voltage_step=-params.get('voltage_step', 0.01),
                scan_rate=params.get('scan_rate', 0.001),
                n_cycles=1
            ),
            LPStep(
                vs_initial=True,
                voltage_step=params.get('voltage_step', 0.01),
                scan_rate=params.get('scan_rate', 0.001),
                n_cycles=1
            )
        ]
        lp_params = LPParams(
            steps=lp_steps,
            record_every_dE=params.get('record_every_dE', 0.0001)
        )
        return LPTechnique(lp_params)
    
    else:
        raise ValueError(f"不支持的技术类型: {technique_type}")

def create_technique_from_simple_config(config):
    """从简化配置创建技术对象"""
    technique_type = config['technique'].lower()
    
    if technique_type == "ocv":
        ocv_params = OCVParams(
            rest_time=config.get('duration', 60),
            record_every_dt=config.get('record_interval', 0.1)
        )
        return OCVTechnique(ocv_params)
    
    elif technique_type == "cv":
        voltage_range = config.get('voltage_range', [-0.5, 0.5])
        cv_steps = [
            CVStep(
                vs_initial=False,
                voltage_step=voltage_range[1] - voltage_range[0],
                scan_rate=config.get('scan_rate', 0.05),
                n_cycles=config.get('cycles', 3)
            )
        ]
        cv_params = CVParams(
            steps=cv_steps,
            n_cycles=config.get('cycles', 3),
            record_every_dE=config.get('record_interval', 0.001)
        )
        return CVTechnique(cv_params)
    
    elif technique_type == "peis":
        freq_range = config.get('frequency_range', [100000, 0.1])
        peis_params = PEISParams(
            vs_initial=False,
            initial_voltage_step=config.get('voltage', 0.0),
            final_frequency=freq_range[1],
            initial_frequency=freq_range[0],
            sweep=SweepMode.Logarithmic,
            amplitude_voltage=config.get('amplitude', 0.01),
            frequency_number=config.get('points', 50)
        )
        return PEISTechnique(peis_params)
    
    elif technique_type == "cp":
        cp_steps = [
            CPStep(
                current=config.get('current', 0.001),
                duration=config.get('duration', 30),
                vs_initial=False
            )
        ]
        cp_params = CPParams(
            steps=cp_steps,
            record_every_dt=config.get('record_interval', 0.1)
        )
        return CPTechnique(cp_params)
    
    elif technique_type == "lp":
        voltage_step = config.get('voltage_step', 0.01)
        lp_steps = [
            LPStep(
                vs_initial=True,
                voltage_step=-voltage_step,
                scan_rate=config.get('scan_rate', 0.001),
                n_cycles=1
            ),
            LPStep(
                vs_initial=True,
                voltage_step=voltage_step,
                scan_rate=config.get('scan_rate', 0.001),
                n_cycles=1
            )
        ]
        lp_params = LPParams(
            steps=lp_steps,
            record_every_dE=config.get('record_interval', 0.0001)
        )
        return LPTechnique(lp_params)
    
    else:
        raise ValueError(f"不支持的技术类型: {technique_type}")

async def run_experiment(config, use_mock=False):
    """运行多技术实验"""
    try:
        # 创建实验ID和路径
        experiment_id = config.get('data_saving', {}).get('experiment_id', 'auto')
        if experiment_id == 'auto':
            experiment_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_multi_tech"
        
        base_dir = config.get('data_saving', {}).get('directory', 'data/experiments')
        experiment_path = os.path.join(os.getcwd(), base_dir, experiment_id)
        
        # 创建实验配置
        exp_config = create_experiment_config(experiment_id, experiment_path)
        
        # 创建WebSocket服务器
        web_dir = os.path.join(os.path.dirname(__file__), 'web')
        vis_config = config.get('visualization', {})
        server = WebSocketServer(
            host=vis_config.get('host', '0.0.0.0'),
            port=vis_config.get('port', 8765),
            static_dir=web_dir
        )
        
        # 启动WebSocket服务器
        await server.start()
        logger.info(f"WebSocket服务器已启动: http://{vis_config.get('host', '0.0.0.0')}:{vis_config.get('port', 8765)}")
        
        # 创建实验控制器
        controller = ExperimentController(exp_config)
        
        # 创建WebSocket数据处理器
        ws_handler = WebSocketDataHandler(server)
        
        # 创建技术序列
        techniques = []
        for tech_config in config['sequence']:
            technique = create_technique_from_config(tech_config)
            techniques.append(technique)
            logger.info(f"已添加技术: {tech_config['technique']}")
        
        if use_mock or USE_MOCK:
            # 使用模拟数据
            logger.info("使用模拟数据而不是真实设备")
            from src.core.devices.mock_biologic_device import MockChannel
            channel = MockChannel()
            controller.initialize(channel)
            
            # 添加WebSocket处理器
            controller.data_acquisition.add_handler(ws_handler)
            
            # 运行实验
            logger.info(f"开始运行多技术实验，共{len(techniques)}个技术")
            await controller.run_experiment(techniques)
        else:
            # 使用真实设备
            device_config = config.get('device', {})
            port = device_config.get('port', 'USB0')
            channel_id = device_config.get('channel', 1)
            
            logger.info(f"连接到Biologic设备: {port}, 通道: {channel_id}")
            with connect(port) as bl:
                channel = bl.get_channel(channel_id)
                controller.initialize(channel)
                
                # 添加WebSocket处理器
                controller.data_acquisition.add_handler(ws_handler)
                
                # 运行实验
                logger.info(f"开始运行多技术实验，共{len(techniques)}个技术")
                await controller.run_experiment(techniques)
        
        logger.info("实验完成")
        
        # 保持服务器运行
        logger.info("实验已完成。服务器仍在运行。按Ctrl+C退出。")
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("收到键盘中断。正在关闭...")
    except Exception as e:
        logger.error(f"运行实验时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # 停止WebSocket服务器
        if 'server' in locals():
            await server.stop()
        logger.info("服务器已停止")

async def main():
    """主函数"""
    args = parse_arguments()
    
    # 加载配置
    config = load_config(args.config)
    
    # 运行实验
    await run_experiment(config, args.mock)

if __name__ == "__main__":
    # 确保目录存在
    os.makedirs("templates", exist_ok=True)
    
    asyncio.run(main())
