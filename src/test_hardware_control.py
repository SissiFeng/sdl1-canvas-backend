"""
hardware control module test script
"""

import os
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@dataclass
class MockLabwarePosition:
    """simulated labware position information"""
    well: str
    x: float
    y: float
    z: float

class MockOT2Controller:
    """simulated OT2 controller"""
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
        """simulate connecting to OT2"""
        await asyncio.sleep(1)  # simulate connection delay
        self.connected = True
        self.logger.info(f"connected to simulated OT2: {ip}")
        return True

    async def move_to_well(self, well: str):
        """simulate moving to specified well"""
        if well not in self.labware_positions:
            raise ValueError(f"unknown well: {well}")
        
        pos = self.labware_positions[well]
        self.logger.info(f"moving to well {well}: (x={pos.x}, y={pos.y}, z={pos.z})")
        await asyncio.sleep(0.5)  # simulate movement time
        self.current_position = {'x': pos.x, 'y': pos.y, 'z': pos.z}
        return True

class MockArduinoController:
    """simulated Arduino controller"""
    def __init__(self):
        self.connected = False
        self.current_position = 0
        self.logger = logging.getLogger(__name__)

    async def connect(self, port: str = "COM1"):
        """simulate connecting to Arduino"""
        await asyncio.sleep(0.5)  # simulate connection delay
        self.connected = True
        self.logger.info(f"connected to simulated Arduino: {port}")
        return True

    async def move_electrode(self, position: int):
        """simulate electrode movement"""
        self.logger.info(f"electrode movement: {self.current_position} -> {position}")
        await asyncio.sleep(0.3)  # simulate movement time
        self.current_position = position
        return True

class ExperimentSimulator:
    """experiment flow simulator"""
    def __init__(self):
        self.ot2 = MockOT2Controller()
        self.arduino = MockArduinoController()
        self.logger = logging.getLogger(__name__)

    async def setup(self):
        """initialize devices"""
        await self.ot2.connect("192.168.1.100")
        await self.arduino.connect("/dev/ttyUSB0")

    async def run_test_sequence(self):
        """run test sequence"""
        # test OT2 movement
        wells = ['A1', 'B1', 'C1']
        for well in wells:
            self.logger.info(f"=== testing moving to well {well} ===")
            await self.ot2.move_to_well(well)
            
            # test electrode movement
            self.logger.info("=== testing electrode operation ===")
            await self.arduino.move_electrode(0)  # electrode up
            await asyncio.sleep(1)
            await self.arduino.move_electrode(100)  # electrode down
            await asyncio.sleep(1)

async def main():
    """main test function"""
    simulator = ExperimentSimulator()
    
    try:
        logger.info("starting hardware control test")
        await simulator.setup()
        await simulator.run_test_sequence()
        logger.info("test completed")
    except Exception as e:
        logger.error(f"error during test: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("test interrupted by user") 
