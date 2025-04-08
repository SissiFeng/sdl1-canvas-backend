"""
模拟的 Arduino 设备接口
"""

import asyncio
import logging
from typing import Optional

class ArduinoDevice:
    """模拟的 Arduino 设备类"""
    def __init__(self, port: Optional[str] = None):
        self.port = port
        self.connected = False
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """模拟连接到设备"""
        await asyncio.sleep(1)  # 模拟连接延迟
        self.connected = True
        self.logger.info(f"Connected to Arduino at {self.port}")
    
    async def disconnect(self) -> None:
        """模拟断开设备连接"""
        await asyncio.sleep(0.5)  # 模拟断开延迟
        self.connected = False
        self.logger.info("Disconnected from Arduino")
    
    def dispense_ml(self, pump_number: int, volume: float) -> None:
        """模拟泵的分配操作"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Dispensing {volume}mL using pump {pump_number}")
        
    def set_ultrasonic(self, state: bool) -> None:
        """模拟超声波清洗器控制"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Setting ultrasonic {'on' if state else 'off'}")
    
    def set_ultrasonic_timer(self, channel: int, duration: int) -> None:
        """模拟超声波清洗器定时器设置"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Setting ultrasonic timer on channel {channel} for {duration}ms")
