"""
硬件控制模块测试脚本
"""

import os
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@dataclass
class MockLabwarePosition:
    """模拟的labware位置信息"""
    well: str
    x: float
    y: float
    z: float

class MockOT2Controller:
    """模拟的OT2控制器"""
    def __init__(self):
        self.connected = False
        self.current_position = {'x': 0, 'y': 0, 'z': 0}
        self.labware_positions = {
            'A1': MockLabwarePosition('A1', 10, 10, 0),
            'B1': MockLabwarePosition('B1', 20, 10, 0),
            'C1': MockLabwarePosition('C1', 30, 10, 0),
        }
        self.logger = logging.getLogger(__name__)

    async def connect(self, ip: str = "localhost"):
        """模拟连接到OT2"""
        await asyncio.sleep(1)  # 模拟连接延迟
        self.connected = True
        self.logger.info(f"已连接到模拟OT2: {ip}")
        return True

    async def move_to_well(self, well: str):
        """模拟移动到指定孔位"""
        if well not in self.labware_positions:
            raise ValueError(f"未知的孔位: {well}")
        
        pos = self.labware_positions[well]
        self.logger.info(f"移动到孔位 {well}: (x={pos.x}, y={pos.y}, z={pos.z})")
        await asyncio.sleep(0.5)  # 模拟移动时间
        self.current_position = {'x': pos.x, 'y': pos.y, 'z': pos.z}
        return True

class MockArduinoController:
    """模拟的Arduino控制器"""
    def __init__(self):
        self.connected = False
        self.current_position = 0
        self.logger = logging.getLogger(__name__)

    async def connect(self, port: str = "COM1"):
        """模拟连接到Arduino"""
        await asyncio.sleep(0.5)  # 模拟连接延迟
        self.connected = True
        self.logger.info(f"已连接到模拟Arduino: {port}")
        return True

    async def move_electrode(self, position: int):
        """模拟电极移动"""
        self.logger.info(f"电极移动: {self.current_position} -> {position}")
        await asyncio.sleep(0.3)  # 模拟移动时间
        self.current_position = position
        return True

class ExperimentSimulator:
    """实验流程模拟器"""
    def __init__(self):
        self.ot2 = MockOT2Controller()
        self.arduino = MockArduinoController()
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """初始化设备"""
        await self.ot2.connect("192.168.1.100")
        await self.arduino.connect("/dev/ttyUSB0")

    async def run_test_sequence(self):
        """运行测试序列"""
        # 测试OT2移动
        wells = ['A1', 'B1', 'C1']
        for well in wells:
            self.logger.info(f"=== 测试移动到孔位 {well} ===")
            await self.ot2.move_to_well(well)
            
            # 测试电极移动
            self.logger.info("=== 测试电极操作 ===")
            await self.arduino.move_electrode(0)  # 电极上升
            await asyncio.sleep(1)
            await self.arduino.move_electrode(100)  # 电极下降
            await asyncio.sleep(1)

async def main():
    """主测试函数"""
    simulator = ExperimentSimulator()
    
    try:
        logger.info("开始硬件控制测试")
        await simulator.setup()
        await simulator.run_test_sequence()
        logger.info("测试完成")
    except Exception as e:
        logger.error(f"测试过程出错: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("测试被用户中断") 
