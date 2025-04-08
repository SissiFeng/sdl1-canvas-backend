"""
Experiment manager for coordinating device controllers and managing experiment workflow.
"""
from typing import Optional, List, Dict, Any
import os
import time
from datetime import datetime

from src.core.devices.opentrons_device import OpentronsDevice
from src.core.devices.arduino_device import ArduinoDevice
from src.core.devices.biologic_device import BiologicDevice
from src.config.device_config import DeviceConfig
from src.config.experiment_config import ExperimentConfig
from src.utils.logging_utils import ExperimentLogger
from src.utils.data_utils import ExperimentDataManager

class ExperimentManager:
    """Manager for automated electrochemical experiments"""
    
    def __init__(self,
                 device_config: DeviceConfig,
                 experiment_config: ExperimentConfig,
                 logger: Optional[ExperimentLogger] = None):
        """
        Initialize experiment manager
        
        Parameters
        ----------
        device_config : DeviceConfig
            Configuration for all devices
        experiment_config : ExperimentConfig
            Configuration for experiment parameters
        logger : Optional[ExperimentLogger]
            Logger instance for experiment
        """
        self.config = experiment_config
        self.logger = logger
        
        # Initialize data manager
        self.data_manager = ExperimentDataManager(
            experiment_id=experiment_config.experiment_id,
            base_dir=experiment_config.experiment_path
        )
        
        # Initialize device controllers
        self.opentrons = OpentronsDevice(device_config.opentrons_config, logger)
        self.arduino = ArduinoDevice(device_config.arduino_config, logger)
        self.biologic = BiologicDevice(
            device_config.biologic_config,
            self.data_manager,
            logger
        )
        
        self.log("info", "Experiment manager initialized")
        
    def log(self, level: str, message: str) -> None:
        """Log message if logger is available"""
        if self.logger:
            getattr(self.logger, level)(message)
            
    def setup_devices(self) -> None:
        """Initialize and connect all devices"""
        try:
            # Connect to Opentrons
            self.log("info", "Connecting to Opentrons...")
            self.opentrons.connect()
            self.opentrons.load_labware()
            self.opentrons.home()
            
            # Connect to Arduino
            self.log("info", "Connecting to Arduino...")
            self.arduino.connect()
            
            # Connect to Biologic
            self.log("info", "Connecting to Biologic...")
            self.biologic.connect()
            
            self.log("info", "All devices connected successfully")
            
        except Exception as e:
            self.log("error", f"Failed to setup devices: {str(e)}")
            self.cleanup()
            raise
            
    def cleanup(self) -> None:
        """Cleanup and disconnect all devices"""
        try:
            if self.opentrons.is_connected:
                self.opentrons.home()
                self.opentrons.lights(False)
                self.opentrons.disconnect()
                
            if self.arduino.is_connected:
                self.arduino.disconnect()
                
            if self.biologic.is_connected:
                self.biologic.disconnect()
                
            self.log("info", "All devices disconnected")
            
        except Exception as e:
            self.log("error", f"Error during cleanup: {str(e)}")
            
    def run_deposition(self) -> None:
        """Run electrodeposition experiment"""
        try:
            self.log("info", "Starting deposition experiment...")
            
            # Prepare well with solution
            self._prepare_well_for_deposition()
            
            # Setup electrode
            self._setup_electrode()
            
            # Run deposition techniques
            techniques = self._create_deposition_techniques()
            self.biologic.run_techniques(techniques, data_type="deposition")
            
            # Clean electrode
            self._clean_electrode()
            
            # Rinse well
            self._rinse_well()
            
            self.log("info", "Deposition experiment completed")
            
        except Exception as e:
            self.log("error", f"Error during deposition: {str(e)}")
            raise
            
    def run_characterization(self) -> None:
        """Run characterization experiment"""
        try:
            self.log("info", "Starting characterization experiment...")
            
            # Prepare well with KOH
            self._prepare_well_for_characterization()
            
            # Setup electrode
            self._setup_electrode()
            
            # Run characterization techniques in batches
            self._run_characterization_batch1()
            self._run_characterization_batch2()
            self._run_characterization_batch3()
            
            # Clean electrode
            self._clean_electrode()
            
            # Rinse well
            self._rinse_well()
            
            self.log("info", "Characterization experiment completed")
            
        except Exception as e:
            self.log("error", f"Error during characterization: {str(e)}")
            raise
            
    def _prepare_well_for_deposition(self) -> None:
        """Prepare well with deposition solution"""
        self.opentrons.pick_up_tip()
        self.opentrons.transfer_solution(
            source_labware="vial_rack_2",
            source_well="B1",
            dest_labware="nis_reactor",
            dest_well=self.config.well_to_test,
            volume=3000
        )
        self.opentrons.drop_tip()
        
    def _prepare_well_for_characterization(self) -> None:
        """Prepare well with KOH solution"""
        self.opentrons.pick_up_tip()
        self.opentrons.transfer_solution(
            source_labware="vial_rack_2",
            source_well="B2",
            dest_labware="nis_reactor",
            dest_well=self.config.well_to_test,
            volume=3000
        )
        self.opentrons.drop_tip()
        
    def _setup_electrode(self) -> None:
        """Setup electrode in well"""
        self.opentrons.pick_up_electrode()
        self.arduino.rinse_electrode()
        self.opentrons.move_electrode_to_well(
            self.config.well_to_test,
            z_offset=-21
        )
        
    def _clean_electrode(self) -> None:
        """Clean electrode after experiment"""
        self.arduino.wash_electrode()
        self.opentrons.return_electrode()
        
    def _rinse_well(self) -> None:
        """Rinse well after experiment"""
        self.opentrons.pick_up_tip()
        
        for _ in range(3):
            self.arduino.dispense_ml(
                self.arduino.config.nozzle['out'],
                volume=1
            )
            self.arduino.dispense_ml(
                self.arduino.config.nozzle['water'],
                volume=1
            )
            self.arduino.dispense_ml(
                self.arduino.config.nozzle['out'],
                volume=3
            )
            
        self.opentrons.drop_tip()
        
    def _create_deposition_techniques(self) -> List[Any]:
        """Create deposition technique sequence"""
        techniques = []
        
        # Add OCV technique
        techniques.append(self.biologic.create_ocv_technique(
            rest_time=60,
            record_every_dt=0.5
        ))
        
        # Add CP technique
        techniques.append(self.biologic.create_cp_technique(
            current=self.config.deposition_config.current,
            duration=self.config.deposition_config.duration,
            record_every_dt=self.config.deposition_config.record_interval
        ))
        
        # Add final OCV
        techniques.append(self.biologic.create_ocv_technique(
            rest_time=60,
            record_every_dt=0.5
        ))
        
        return techniques
        
    def _run_characterization_batch1(self) -> None:
        """Run first batch of characterization techniques"""
        techniques = []
        cv_config = self.config.characterization_config.cv_params
        
        # Add initial OCV
        techniques.append(self.biologic.create_ocv_technique(
            rest_time=10
        ))
        
        # Add CV techniques with different scan rates
        for scan_rate in [0.02, 0.04, 0.06, 0.08, 0.1]:
            techniques.append(self.biologic.create_cv_technique(
                voltage_steps=cv_config.get_voltage_steps(scan_rate),
                n_cycles=3
            ))
            
        # Add PEIS techniques
        peis_config = self.config.characterization_config.peis_params
        techniques.extend([
            self.biologic.create_peis_technique(**peis_config.no_oer_params),
            self.biologic.create_peis_technique(**peis_config.oer_params)
        ])
        
        # Add redox and active CV
        techniques.extend([
            self.biologic.create_cv_technique(**cv_config.redox_params),
            self.biologic.create_cv_technique(**cv_config.active_params)
        ])
        
        self.biologic.run_techniques(techniques, "characterization")
        
    def _run_characterization_batch2(self) -> None:
        """Run second batch of characterization techniques"""
        techniques = []
        
        # Add PEIS techniques
        peis_config = self.config.characterization_config.peis_params
        techniques.extend([
            self.biologic.create_peis_technique(**peis_config.no_oer_params),
            self.biologic.create_peis_technique(**peis_config.oer_params)
        ])
        
        # Add redox CV and LSV
        cv_config = self.config.characterization_config.cv_params
        techniques.extend([
            self.biologic.create_cv_technique(**cv_config.redox_params),
            self.biologic.create_lp_technique(
                **self.config.characterization_config.lsv_params
            )
        ])
        
        self.biologic.run_techniques(techniques, "characterization")
        
    def _run_characterization_batch3(self) -> None:
        """Run third batch of characterization techniques"""
        techniques = []
        cv_config = self.config.characterization_config.cv_params
        
        # Add stability test
        techniques.append(self.biologic.create_cv_technique(
            **cv_config.stability_params
        ))
        
        # Add OCV
        techniques.append(self.biologic.create_ocv_technique(
            rest_time=10
        ))
        
        # Add CV techniques with different scan rates
        for scan_rate in [0.02, 0.04, 0.06, 0.08, 0.1]:
            techniques.append(self.biologic.create_cv_technique(
                voltage_steps=cv_config.get_voltage_steps(scan_rate),
                n_cycles=3
            ))
            
        # Add PEIS techniques
        peis_config = self.config.characterization_config.peis_params
        techniques.extend([
            self.biologic.create_peis_technique(**peis_config.no_oer_params),
            self.biologic.create_peis_technique(**peis_config.oer_params)
        ])
        
        # Add final redox CV
        techniques.append(self.biologic.create_cv_technique(
            **cv_config.redox_params
        ))
        
        self.biologic.run_techniques(techniques, "characterization") 
