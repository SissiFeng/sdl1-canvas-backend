"""
simulated Opentrons device interface
"""

import asyncio
import logging
from typing import Optional

class OpentronsDevice:
    """simulated Opentrons device class"""
    def __init__(self, robot_ip: str = "100.67.89.154"):
        self.robot_ip = robot_ip
        self.connected = False
        self.logger = logging.getLogger(__name__)
    
    async def connect(self) -> None:
        """simulate connecting to the device"""
        await asyncio.sleep(1)  # simulate connection delay
        self.connected = True
        self.logger.info(f"Connected to Opentrons at {self.robot_ip}")
    
    async def disconnect(self) -> None:
        """simulate disconnecting from the device"""
        await asyncio.sleep(0.5)  # simulate disconnection delay
        self.connected = False
        self.logger.info("Disconnected from Opentrons")
    
    def move_to_well(self, labware_name: str, well_name: str, pipette_name: str,
                    offset_start: str = 'top', offset_x: float = 0,
                    offset_y: float = 0, offset_z: float = 0,
                    speed: int = 100) -> None:
        """simulate moving to the specified position"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Moving to well {well_name} in {labware_name}")
    
    def pick_up_tip(self, labware_name: str, well_name: str,
                    pipette_name: str) -> None:
        """simulate picking up the tip"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Picking up tip from {well_name} in {labware_name}")
    
    def drop_tip(self, labware_name: str, well_name: str,
                 pipette_name: str) -> None:
        """simulate dropping the tip"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Dropping tip to {well_name} in {labware_name}")
    
    def aspirate(self, labware_name: str, well_name: str,
                pipette_name: str, volume: float) -> None:
        """simulate aspirating the liquid"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Aspirating {volume}µL from {well_name} in {labware_name}")
    
    def dispense(self, labware_name: str, well_name: str,
                pipette_name: str, volume: float) -> None:
        """simulate dispensing the liquid"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Dispensing {volume}µL to {well_name} in {labware_name}")
    
    def home_robot(self) -> None:
        """simulate homing"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info("Homing robot")
    
    def set_lights(self, state: bool) -> None:
        """simulate setting the lights"""
        if not self.connected:
            raise RuntimeError("Device not connected")
        self.logger.info(f"Setting lights {'on' if state else 'off'}") 
