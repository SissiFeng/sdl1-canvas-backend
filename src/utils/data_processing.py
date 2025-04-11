"""
data processing module, for processing the data of electrochemical experiments, including real-time data processing and display.
"""

import os
import asyncio
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import json

@dataclass
class ExperimentConfig:
    """experiment configuration data class"""
    experiment_id: str
    base_path: str
    deposition_path: str
    characterization_path: str

class DataHandler:
    """data handler abstract base class"""
    async def handle_data(self, data: Any) -> None:
        pass

class DataAcquisitionModule:
    """data acquisition module"""
    def __init__(self, channel, experiment_config: ExperimentConfig):
        self.channel = channel
        self.config = experiment_config
        self.data_handlers: List[DataHandler] = []
        self.logger = logging.getLogger(__name__)

    def add_handler(self, handler: DataHandler) -> None:
        """add data handler"""
        self.data_handlers.append(handler)

    async def notify_handlers(self, data: Any) -> None:
        """notify all handlers"""
        for handler in self.data_handlers:
            try:
                await handler.handle_data(data)
            except Exception as e:
                self.logger.error(f"Handler {handler.__class__.__name__} failed: {str(e)}")

    async def start_acquisition(self, techniques: List[Any]):
        """start data acquisition"""
        try:
            runner = self.channel.run_techniques(techniques)
            async for data in runner:
                await self.notify_handlers(data)
                yield data
        except Exception as e:
            self.logger.error(f"Data acquisition failed: {str(e)}")
            raise

class DataProcessor(DataHandler):
    """data processing module"""
    def __init__(self):
        self.current_technique = None
        self.tech_index = 0
        self.tech_add = 0
        self.current_df = pd.DataFrame()
        self.logger = logging.getLogger(__name__)

    async def handle_data(self, data: Any) -> pd.DataFrame:
        """process data and return DataFrame"""
        try:
            if hasattr(data.data, 'process_data'):
                return self._process_indexed_data(data)
            return self._process_regular_data(data)
        except Exception as e:
            self.logger.error(f"Data processing failed: {str(e)}")
            raise

    def _process_indexed_data(self, data: Any) -> pd.DataFrame:
        """process indexed data"""
        return pd.DataFrame(data.data.process_data.to_json(), index=[0])

    def _process_regular_data(self, data: Any) -> pd.DataFrame:
        """process regular data"""
        return pd.DataFrame(data.data.to_json(), index=[0])

    def get_technique_name(self, data: Any) -> str:
        """get technique name"""
        return str(type(data.data)).split("'")[1].split(".")[-2]

class DataStorage(DataHandler):
    """data storage module"""
    def __init__(self, experiment_config: ExperimentConfig):
        self.config = experiment_config
        self.logger = logging.getLogger(__name__)

    async def handle_data(self, data: Any) -> None:
        """process and store data"""
        try:
            processor = DataProcessor()
            processed_data = await processor.handle_data(data)
            self.save_data(processed_data, data.tech_index, self.get_technique_type(data))
        except Exception as e:
            self.logger.error(f"Data storage failed: {str(e)}")
            raise

    def save_data(self, data: pd.DataFrame, technique_id: int, technique_name: str) -> None:
        """save data to file"""
        filename = f'{self.config.experiment_id}_{technique_id}_{technique_name}.csv'
        filepath = os.path.join(self.config.characterization_path, filename)
        data.to_csv(filepath, index=False)
        self.logger.info(f"Saved data to {filepath}")

    def load_data(self, technique_id: int, technique_name: str) -> pd.DataFrame:
        """load data from file"""
        filename = f'{self.config.experiment_id}_{technique_id}_{technique_name}.csv'
        filepath = os.path.join(self.config.characterization_path, filename)
        return pd.read_csv(filepath)

    @staticmethod
    def get_technique_type(data: Any) -> str:
        """get technique type"""
        return str(type(data.data)).split("'")[1].split(".")[-2]

class RealTimeVisualizer(DataHandler):
    """real-time visualization module"""
    def __init__(self):
        # set backend
        import matplotlib
        matplotlib.use('TkAgg')
        
        plt.ion()  # enable interactive mode
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        
        # initialize data storage
        self.data_cache = {}
        self.lines = {}
        self.technique_plots = {
            'CV': self._setup_cv_plot,
            'PEIS': self._setup_eis_plot,
            'OCV': self._setup_ocv_plot,
            'CP': self._setup_cp_plot,
            'LP': self._setup_lp_plot,
            'MockOCVTechnique': self._setup_ocv_plot,
            'MockCPTechnique': self._setup_cp_plot,
            'MockPEISTechnique': self._setup_eis_plot,
            'MockCVTechnique': self._setup_cv_plot,
            'MockResult': self._setup_ocv_plot
        }
        
        # configure chart window
        self.figure.canvas.manager.set_window_title('real-time electrochemical data')
        self.current_technique = None
        
        # show chart
        plt.show(block=False)
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("RealTimeVisualizer initialized")

    async def handle_data(self, data: Any) -> None:
        """process and visualize data"""
        try:
            # get technique type
            technique_type = self.get_technique_type(data)
            self.logger.debug(f"detected technique type: {technique_type}")
            
            # extract data
            if hasattr(data, 'data') and hasattr(data.data, 'to_json'):
                json_data = data.data.to_json()
                self.logger.debug(f"received data: {json_data}")
                
                # if it's a new technique type, initialize the chart
                if technique_type != self.current_technique:
                    self.initialize_plot(technique_type)
                    self.current_technique = technique_type
                    self.data_cache[technique_type] = {'x': [], 'y': []}
                    self.lines[technique_type], = self.ax.plot([], [], 'bo-', markersize=4, label=technique_type)
                    self.ax.legend()
                
                # get the latest data point
                x_data, y_data = self._get_plot_data(json_data, technique_type)
                if x_data and y_data:
                    # add to data cache
                    self.data_cache[technique_type]['x'].extend(x_data)
                    self.data_cache[technique_type]['y'].extend(y_data)
                    
                    # update chart
                    self.lines[technique_type].set_data(
                        self.data_cache[technique_type]['x'],
                        self.data_cache[technique_type]['y']
                    )
                    
                    # adjust axis range
                    self.ax.relim()
                    self.ax.autoscale_view()
                    
                    # force redraw
                    self.figure.canvas.draw()
                    self.figure.canvas.flush_events()
                    
                    self.logger.debug(f"updated chart: x={x_data[-1]:.2f}, y={y_data[-1]:.4f}")
                
        except Exception as e:
            self.logger.error(f"visualization error: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())

    def initialize_plot(self, technique_type: str) -> None:
        """initialize chart"""
        self.logger.info(f"initializing chart: {technique_type}")
        
        # clear existing chart
        self.ax.clear()
        
        # set chart based on technique type
        if technique_type in self.technique_plots:
            self.technique_plots[technique_type]()
        else:
            self._setup_default_plot()
        
        # general settings
        self.ax.grid(True)
        self.figure.tight_layout()
        
        # force redraw
        self.figure.canvas.draw()
        plt.pause(0.1)

    def _setup_default_plot(self) -> None:
        """default chart settings"""
        self.ax.set_xlabel('data X')
        self.ax.set_ylabel('data Y')
        self.ax.set_title('electrochemical data')

    def _setup_cv_plot(self) -> None:
        """CV chart settings"""
        self.ax.set_xlabel('voltage (V)')
        self.ax.set_ylabel('current (A)')
        self.ax.set_title('cyclic voltammetry')

    def _setup_eis_plot(self) -> None:
        """EIS chart settings"""
        self.ax.set_xlabel('Re(Z) (Ω)')
        self.ax.set_ylabel('-Im(Z) (Ω)')
        self.ax.set_title('electrochemical impedance spectroscopy')

    def _setup_ocv_plot(self) -> None:
        """OCV chart settings"""
        self.ax.set_xlabel('time (s)')
        self.ax.set_ylabel('voltage (V)')
        self.ax.set_title('open circuit voltage')

    def _setup_cp_plot(self) -> None:
        """CP chart settings"""
        self.ax.set_xlabel('time (s)')
        self.ax.set_ylabel('voltage (V)')
        self.ax.set_title('constant current')

    def _setup_lp_plot(self) -> None:
        """LP chart settings"""
        self.ax.set_xlabel('voltage (V)')
        self.ax.set_ylabel('current (A)')
        self.ax.set_title('linear polarization')

    def _get_plot_data(self, data: Dict[str, Any], technique_type: str) -> Tuple[List[float], List[float]]:
        """get plot data"""
        if not data:
            return [], []
            
        # ensure all data is list format
        processed_data = {}
        for key, value in data.items():
            if isinstance(value, (int, float)):
                processed_data[key] = [value]
            elif isinstance(value, list):
                processed_data[key] = value
            else:
                try:
                    processed_data[key] = list(value)
                except:
                    processed_data[key] = [value]
        
        # extract data based on technique type
        if technique_type in ['CV', 'MockCVTechnique']:
            return processed_data.get('Ewe', []), processed_data.get('I', [])
        elif technique_type in ['PEIS', 'MockPEISTechnique']:
            re_z = processed_data.get('Re(Z)', [])
            im_z = [-im for im in processed_data.get('Im(Z)', [])] if 'Im(Z)' in processed_data else []
            return re_z, im_z
        elif technique_type in ['OCV', 'CP', 'MockOCVTechnique', 'MockCPTechnique', 'MockResult']:
            return processed_data.get('time', []), processed_data.get('Ewe', [])
        elif technique_type == 'LP':
            return processed_data.get('Ewe', []), processed_data.get('I', [])
        else:
            # try to find any numeric array that can be plotted
            for key1 in processed_data:
                if isinstance(processed_data[key1], list) and processed_data[key1]:
                    for key2 in processed_data:
                        if key1 != key2 and isinstance(processed_data[key2], list) and processed_data[key2]:
                            self.logger.info(f"using general data: x={key1}, y={key2}")
                            return processed_data[key1], processed_data[key2]
            return [], []

    @staticmethod
    def get_technique_type(data: Any) -> str:
        """get technique type"""
        if hasattr(data, 'data'):
            data_obj = data.data
            
            # method 1: get class name
            class_name = data_obj.__class__.__name__
            if class_name != 'object':
                return class_name
            
            # method 2: find type attribute
            if hasattr(data_obj, 'type'):
                return data_obj.type
            
            # method 3: find technique type attribute
            if hasattr(data_obj, 'technique_type'):
                return data_obj.technique_type
        
        return "Unknown"

    def __del__(self):
        """clean up resources"""
        try:
            plt.close(self.figure)
            plt.close('all')
        except:
            pass

class ExperimentController:
    """experiment controller"""
    def __init__(self, experiment_config: ExperimentConfig):
        self.config = experiment_config
        self.data_acquisition = None
        self.data_processor = DataProcessor()
        self.data_storage = DataStorage(experiment_config)
        self.visualizer = RealTimeVisualizer()
        self.logger = logging.getLogger(__name__)
        
        # set more detailed log level
        self.logger.setLevel(logging.DEBUG)
        # add console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def initialize(self, channel) -> None:
        """initialize controller"""
        self.logger.info("initializing experiment controller")
        self.data_acquisition = DataAcquisitionModule(channel, self.config)
        
        # directly process data, not through processor
        self.data_acquisition.add_handler(self.visualizer)
        self.data_acquisition.add_handler(self.data_storage)
        
        self.logger.info("data processor added")

    async def run_experiment(self, techniques: List[Any]) -> None:
        """run experiment"""
        try:
            self.logger.info(f"starting experiment {self.config.experiment_id}")
            self.logger.debug(f"technique list: {[t.__class__.__name__ for t in techniques]}")
            
            async for data in self.data_acquisition.start_acquisition(techniques):
                # record each data point
                if hasattr(data, 'data') and hasattr(data.data, 'to_json'):
                    json_data = data.data.to_json()
                    self.logger.debug(f"received data point: {json_data}")
                    
                    # ensure data is correctly processed
                    technique_type = (data.data.__class__.__name__ 
                                   if hasattr(data.data, '__class__') 
                                   else "Unknown")
                    self.logger.debug(f"technique type: {technique_type}")
                    
                    # check data cache
                    if hasattr(self.visualizer, 'data_cache'):
                        cache_info = {k: len(v['x']) for k, v in self.visualizer.data_cache.items()}
                        self.logger.debug(f"visualizer cache status: {cache_info}")
            
            self.logger.info(f"experiment {self.config.experiment_id} completed")
        except Exception as e:
            self.logger.error(f"experiment failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise

def create_experiment_config(experiment_id: str, base_path: str) -> ExperimentConfig:
    """create experiment configuration"""
    deposition_path = os.path.join(base_path, 'deposition')
    characterization_path = os.path.join(base_path, 'characterization')
    
    # ensure directories exist
    os.makedirs(deposition_path, exist_ok=True)
    os.makedirs(characterization_path, exist_ok=True)
    
    return ExperimentConfig(
        experiment_id=experiment_id,
        base_path=base_path,
        deposition_path=deposition_path,
        characterization_path=characterization_path
    ) 

class ExperimentDataManager:
    """experiment data manager"""
    
    def __init__(self, experiment_id: str, base_dir: str):
        self.experiment_id = experiment_id
        self.base_dir = base_dir
        
    def save_technique_data(self, 
                          data: pd.DataFrame,
                          technique_id: int,
                          technique_name: str,
                          data_type: str = "characterization") -> str:
        """
        save technique data to CSV file
        
        Parameters
        ----------
        data : pd.DataFrame
            data to save
        technique_id : int
            technique ID
        technique_name : str
            technique name
        data_type : str
            data type (characterization or deposition)
            
        Returns
        -------
        str
            saved file path
        """
        filename = f"{self.experiment_id}_{technique_id}_{technique_name}.csv"
        save_dir = os.path.join(self.base_dir, data_type)
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)
        
        data.to_csv(filepath, index=False)
        return filepath
    
    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        save experiment metadata to JSON file
        
        Parameters
        ----------
        metadata : Dict[str, Any]
            metadata to save
            
        Returns
        -------
        str
            saved file path
        """
        filename = "metadata.json"
        filepath = os.path.join(self.base_dir, filename)
        os.makedirs(self.base_dir, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        return filepath
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """
        update existing metadata file
        
        Parameters
        ----------
        updates : Dict[str, Any]
            new metadata values
        """
        filepath = os.path.join(self.base_dir, "metadata.json")
        
        # read existing metadata
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}
        
        # update metadata
        metadata.update(updates)
        
        # save updated metadata
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def load_technique_data(self, 
                          technique_id: int,
                          technique_name: str,
                          data_type: str = "characterization") -> Optional[pd.DataFrame]:
        """
        load technique data from CSV file
        
        Parameters
        ----------
        technique_id : int
            technique ID
        technique_name : str
            technique name
        data_type : str
            data type (characterization or deposition)
            
        Returns
        -------
        Optional[pd.DataFrame]
            loaded data, None if file does not exist
        """
        filename = f"{self.experiment_id}_{technique_id}_{technique_name}.csv"
        filepath = os.path.join(self.base_dir, data_type, filename)
        
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        return None
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        load experiment metadata
        
        Returns
        -------
        Optional[Dict[str, Any]]
            metadata, None if file does not exist
        """
        filepath = os.path.join(self.base_dir, "metadata.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None 
