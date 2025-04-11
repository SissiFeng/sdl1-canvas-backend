"""
simulated Arduino device interface
"""

import asyncio
import logging
from typing import Optional

class ArduinoDevice:
    """simulated Arduino device class"""
    def __init__(self, port: Optional[str] = None):
        self.port = port
        self.connected = False
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """simulate connecting to the device"""
        await asyncio.sleep(1)  # simulate connection delay
        self.connected = True
        self.logger.info(f"Connected to Arduino at {self.port}")
    
    async def disconnect(self) -> None:
        """simulate disconnecting from the device"""
        await asyncio.sleep(0.5)  # simulate disconnection delay
        self.connected = False
        self.logger.info("Disconnected from Arduino")
    
    def dispense_ml(self, pump_number: int, volume: float) -> None:
        """simulate the dispensing operation of the pump"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Dispensing {volume}mL using pump {pump_number}")
        
    def set_ultrasonic(self, state: bool) -> None:
        """simulate the control of the ultrasonic cleaner"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Setting ultrasonic {'on' if state else 'off'}")
    
    def set_ultrasonic_timer(self, channel: int, duration: int) -> None:
        """simulate the setting of the ultrasonic cleaner timer"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Setting ultrasonic timer on channel {channel} for {duration}ms")
