"""
Device configuration parameters for the automated electrochemical experiment system.
"""
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class OpentronsConfig:
    """Opentrons robot configuration"""
    robot_ip: str = "100.67.89.154"
    pipette_name: str = "p1000_single_gen2"
    pipette_mount: str = "right"
    
    # Labware slots configuration
    PIPETTE_TIP_RACK_SLOT: int = 1
    VIAL_RACK_SLOTS: list = (2, 7, 11)
    WASH_STATION_SLOT: int = 3
    NIS_REACTOR_SLOT: int = 9
    ELECTRODE_TIP_RACK_SLOT: int = 10

@dataclass
class ArduinoConfig:
    """Arduino pump configuration"""
    nozzle: Dict[str, int] = None
    rinse: Dict[str, int] = None
    
    def __post_init__(self):
        self.nozzle = {
            'water': 1,
            'acid': 0,
            'out': 2,
        }
        self.rinse = {
            'water': 3,
            'acid': 5,
            'out': 4,
        }

@dataclass
class BiologicConfig:
    """Biologic potentiostat configuration"""
    usb_port: str = "USB0"
    channel_id: int = 1
    max_connection_attempts: int = 3
    retry_delay: int = 50  # seconds

@dataclass
class DeviceConfig:
    """Main device configuration container"""
    opentrons: OpentronsConfig = OpentronsConfig()
    arduino: ArduinoConfig = ArduinoConfig()
    biologic: BiologicConfig = BiologicConfig() 
