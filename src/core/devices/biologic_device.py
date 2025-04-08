"""
Biologic device controller for the automated electrochemical experiment system.
"""
from typing import Optional, List, Dict, Any
import time
import pandas as pd

from biologic import connect, BANDWIDTH, I_RANGE, E_RANGE
from biologic.techniques import (
    OCVTechnique, OCVParams,
    PEISTechnique, PEISParams, SweepMode,
    CVTechnique, CVParams, CVStep,
    LPTechnique, LPParams, LPStep,
    CPTechnique, CPParams, CPStep
)

from src.core.devices.base_device import BaseDevice, ConnectionError, OperationError
from src.config.device_config import BiologicConfig
from src.utils.logging_utils import ExperimentLogger
from src.utils.data_utils import ExperimentDataManager

class BiologicDevice(BaseDevice):
    """Controller for Biologic potentiostat"""
    
    def __init__(self, 
                 config: BiologicConfig,
                 data_manager: ExperimentDataManager,
                 logger: Optional[ExperimentLogger] = None):
        super().__init__(logger)
        self.config = config
        self.data_manager = data_manager
        self.client = None
        self.channel = None
        
    def connect(self) -> bool:
        """Connect to Biologic potentiostat"""
        attempts = 0
        while attempts < self.config.max_connection_attempts:
            try:
                self.client = connect(self.config.usb_port)
                self.channel = self.client.get_channel(self.config.channel_id)
                self.connected = True
                self.log("info", f"Connected to Biologic on {self.config.usb_port}")
                return True
            except Exception as e:
                attempts += 1
                self.log("warning", 
                    f"Connection attempt {attempts} failed: {str(e)}. "
                    f"Retrying in {self.config.retry_delay} seconds..."
                )
                time.sleep(self.config.retry_delay)
                
        raise ConnectionError("Failed to connect to Biologic after maximum attempts")
    
    def disconnect(self) -> bool:
        """Disconnect from Biologic potentiostat"""
        try:
            if self.client:
                self.client.close()
                self.client = None
                self.channel = None
                self.connected = False
                self.log("info", "Disconnected from Biologic")
            return True
        except Exception as e:
            raise ConnectionError(f"Failed to disconnect from Biologic: {str(e)}")
    
    def run_techniques(self, techniques: List[Any], data_type: str = "characterization") -> None:
        """
        Run a sequence of electrochemical techniques
        
        Parameters
        ----------
        techniques : List[Any]
            List of technique objects to run
        data_type : str
            Type of data being collected (characterization or deposition)
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Biologic")
            
        try:
            # Initialize data collection
            df_data = pd.DataFrame()
            tech_id = 0
            tech_id_add = 0
            current_technique = ""
            first_technique = True
            
            # Run techniques
            runner = self.channel.run_techniques(techniques)
            
            for data in runner:
                # Handle first technique
                if first_technique:
                    current_technique = self._get_technique_name(data)
                    first_technique = False
                
                # Check for new technique
                if data.tech_index != tech_id:
                    # Save current data
                    if not df_data.empty:
                        self.data_manager.save_technique_data(
                            data=df_data,
                            technique_id=tech_id + tech_id_add,
                            technique_name=current_technique,
                            data_type=data_type
                        )
                        df_data = pd.DataFrame()
                    
                    # Update technique tracking
                    tech_id = data.tech_index
                    current_technique = self._get_technique_name(data)
                
                # Process data
                if 'process_index' in data.data.to_json():
                    df_temp = pd.DataFrame(data.data.process_data.to_json(), index=[0])
                else:
                    df_temp = pd.DataFrame(data.data.to_json(), index=[0])
                
                # Log data point
                self.log("debug", str(data))
                
                # Append to dataframe
                df_data = pd.concat([df_data, df_temp], ignore_index=True)
            
            # Save final dataset
            if not df_data.empty:
                self.data_manager.save_technique_data(
                    data=df_data,
                    technique_id=tech_id + tech_id_add,
                    technique_name=current_technique,
                    data_type=data_type
                )
            
            self.log("info", f"Completed running {len(techniques)} techniques")
            
        except Exception as e:
            raise OperationError(f"Failed to run techniques: {str(e)}")
    
    def _get_technique_name(self, data: Any) -> str:
        """Extract technique name from data object"""
        return str(type(data.data)).split("'")[1].split(".")[-2]
    
    def create_ocv_technique(self, 
                           rest_time: float,
                           record_every_dt: float = 0.5,
                           record_every_de: float = 10,
                           e_range: E_RANGE = E_RANGE.E_RANGE_2_5V,
                           bandwidth: BANDWIDTH = BANDWIDTH.BW_5) -> OCVTechnique:
        """Create Open Circuit Voltage technique"""
        params = OCVParams(
            rest_time_T=rest_time,
            record_every_dT=record_every_dt,
            record_every_dE=record_every_de,
            E_range=e_range,
            bandwidth=bandwidth
        )
        return OCVTechnique(params)
    
    def create_peis_technique(self,
                            initial_voltage: float,
                            duration: float,
                            final_frequency: float,
                            initial_frequency: float,
                            amplitude: float,
                            num_points: int,
                            vs_initial: bool = False,
                            average_n_times: int = 2,
                            bandwidth: BANDWIDTH = BANDWIDTH.BW_5,
                            e_range: E_RANGE = E_RANGE.E_RANGE_2_5V) -> PEISTechnique:
        """Create Potentio Electrochemical Impedance Spectroscopy technique"""
        params = PEISParams(
            vs_initial=vs_initial,
            initial_voltage_step=initial_voltage,
            duration_step=duration,
            final_frequency=final_frequency,
            initial_frequency=initial_frequency,
            amplitude_voltage=amplitude,
            frequency_number=num_points,
            average_n_times=average_n_times,
            correction=False,
            wait_for_steady=0.1,
            bandwidth=bandwidth,
            E_range=e_range
        )
        return PEISTechnique(params)
    
    def create_cv_technique(self,
                          voltage_steps: List[Dict[str, Any]],
                          record_every_de: float = 0.01,
                          n_cycles: int = 3,
                          bandwidth: BANDWIDTH = BANDWIDTH.BW_5,
                          i_range: I_RANGE = I_RANGE.I_RANGE_10mA) -> CVTechnique:
        """Create Cyclic Voltammetry technique"""
        steps = []
        for step in voltage_steps:
            steps.append(CVStep(
                voltage=step['voltage'],
                scan_rate=step['scan_rate'],
                vs_initial=step.get('vs_initial', False)
            ))
            
        params = CVParams(
            record_every_dE=record_every_de,
            average_over_dE=False,
            n_cycles=n_cycles,
            begin_measuring_i=0.5,
            end_measuring_i=1,
            Ei=steps[0],
            E1=steps[1],
            E2=steps[2],
            Ef=steps[3],
            bandwidth=bandwidth,
            I_range=i_range
        )
        return CVTechnique(params)
    
    def create_cp_technique(self,
                          current: float,
                          duration: float,
                          record_every_dt: float = 0.1,
                          record_every_de: float = 0.05,
                          vs_initial: bool = False,
                          i_range: I_RANGE = I_RANGE.I_RANGE_10mA) -> CPTechnique:
        """Create Chronopotentiometry technique"""
        step = CPStep(
            current=current,
            duration=duration,
            vs_initial=vs_initial
        )
        
        params = CPParams(
            record_every_dT=record_every_dt,
            record_every_dE=record_every_de,
            n_cycles=0,
            steps=[step],
            I_range=i_range
        )
        return CPTechnique(params)
    
    def create_lp_technique(self,
                          voltage_steps: List[Dict[str, Any]],
                          rest_time: float = 5,
                          record_every_dt: float = 0.5,
                          record_every_de: float = 0.001,
                          i_range: I_RANGE = I_RANGE.I_RANGE_100mA,
                          e_range: E_RANGE = E_RANGE.E_RANGE_2_5V) -> LPTechnique:
        """Create Linear Polarization technique"""
        steps = []
        for step in voltage_steps:
            steps.append(LPStep(
                voltage_scan=step['voltage'],
                scan_rate=step['scan_rate'],
                vs_initial_scan=step.get('vs_initial', False)
            ))
            
        params = LPParams(
            record_every_dEr=0.01,
            rest_time_T=rest_time,
            record_every_dTr=record_every_dt,
            Ei=steps[0],
            El=steps[1],
            record_every_dE=record_every_de,
            average_over_dE=False,
            begin_measuring_I=0.5,
            end_measuring_I=1,
            I_range=i_range,
            E_range=e_range
        )
        return LPTechnique(params) 
