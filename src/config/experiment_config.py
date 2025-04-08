"""
Experiment configuration parameters for the automated electrochemical experiment system.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
import os

@dataclass
class ExperimentConfig:
    """Experiment configuration parameters"""
    # Basic experiment parameters
    run_number: str = "001"
    well_to_test: str = "C5"
    experiment_id: str = None
    
    # Paths and directories
    base_dir: str = os.getcwd()
    data_dir: str = "data"
    labware_dir: str = "labware"
    
    def __post_init__(self):
        # Generate experiment ID if not provided
        if not self.experiment_id:
            current_date = datetime.now().strftime("%Y%m%d")
            self.experiment_id = f"{current_date}_{self.run_number}"
            
        # Setup directory paths
        self.experiment_dir = os.path.join(self.base_dir, self.data_dir, self.experiment_id)
        self.deposition_dir = os.path.join(self.experiment_dir, 'deposition')
        self.characterization_dir = os.path.join(self.experiment_dir, 'characterization')
        
    def create_directories(self):
        """Create necessary directories for the experiment"""
        os.makedirs(self.experiment_dir, exist_ok=True)
        os.makedirs(self.deposition_dir, exist_ok=True)
        os.makedirs(self.characterization_dir, exist_ok=True)
        
    def get_metadata(self) -> Dict[str, Any]:
        """Generate experiment metadata"""
        return {
            "date": datetime.now().strftime("%Y%m%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "runNumber": self.run_number,
            "experimentID": self.experiment_id,
            "cell": self.well_to_test,
            "status": "running",
            "notes": "Ni(NO3)2 9H2O electrodeposition on C paper (Top) and basic OER"
        }

@dataclass
class DepositionConfig:
    """Configuration for deposition experiments"""
    current: float = -0.002  # A
    duration: int = 60  # seconds
    record_interval: float = 0.1  # seconds
    voltage_record_interval: float = 0.05  # V

@dataclass
class CharacterizationConfig:
    """Configuration for characterization experiments"""
    # CV parameters
    cv_scan_rates: list = (0.02, 0.04, 0.06, 0.08, 0.1)  # V/s
    cv_voltage_range: tuple = (-0.05, 0.05)  # V
    cv_cycles: int = 3
    
    # PEIS parameters
    peis_frequency_range: tuple = (1, 200000)  # Hz
    peis_voltage_amplitude: float = 0.01  # V
    peis_points: int = 60
    
    # Stability test parameters
    stability_voltage_range: tuple = (0.6, 1.0)  # V
    stability_scan_rate: float = 0.025  # V/s
    stability_cycles: int = 50 
