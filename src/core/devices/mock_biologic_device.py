"""
simulated Biologic device interface
"""

import asyncio
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
import logging

@dataclass
class MockData:
    """simulated data class"""
    time: Optional[float] = None
    Ewe: Optional[float] = None
    I: Optional[float] = None
    freq: Optional[float] = None
    Re_Z: Optional[float] = None
    Im_Z: Optional[float] = None
    technique_type: str = ''
    _data: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    _index: int = 0
    _max_points: int = 100
    _last_update_index: int = -1  # track the last updated index
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    def add_current_values_to_data(self):
        """add the current values to the accumulated data"""
        # avoid adding duplicate data points
        if self._index <= self._last_update_index:
            self.logger.debug(f"skipping duplicate data point: index={self._index}")
            return
            
        self._last_update_index = self._index
        
        if self.technique_type == 'MockOCVTechnique':
            if self.time is not None:
                self._data['time'].append(self.time)
            if self.Ewe is not None:
                self._data['Ewe'].append(self.Ewe)
            self.logger.debug(f"adding OCV data point: time={self.time}, Ewe={self.Ewe}")
        elif self.technique_type == 'MockCPTechnique':
            if self.time is not None:
                self._data['time'].append(self.time)
            if self.Ewe is not None:
                self._data['Ewe'].append(self.Ewe)
            self.logger.debug(f"adding CP data point: time={self.time}, Ewe={self.Ewe}")
        elif self.technique_type == 'MockPEISTechnique':
            if self.Re_Z is not None:
                self._data['Re(Z)'].append(self.Re_Z)
            if self.Im_Z is not None:
                self._data['Im(Z)'].append(self.Im_Z)
            self.logger.debug(f"adding PEIS data point: Re_Z={self.Re_Z}, Im_Z={self.Im_Z}")
        elif self.technique_type == 'MockCVTechnique':
            if self.Ewe is not None:
                self._data['Ewe'].append(self.Ewe)
            if self.I is not None:
                self._data['I'].append(self.I)
            self.logger.debug(f"adding CV data point: Ewe={self.Ewe}, I={self.I}")
        
        self.logger.info(f"data point {self._index} added to {self.technique_type}, current data size: {self.get_data_size()}")

    def get_data_size(self) -> str:
        """get the current data size information"""
        sizes = [f"{key}: {len(value)}" for key, value in self._data.items()]
        return ", ".join(sizes)

    def to_json(self) -> Dict[str, List[float]]:
        """return the accumulated data"""
        # ensure the current values are added to the data
        self.add_current_values_to_data()
        # return a copy of the accumulated data
        return {k: list(v) for k, v in self._data.items()}

    async def generate_data(self):
        """generate simulated data"""
        self.logger.info(f"starting to generate {self.technique_type} data")
        while self._index < self._max_points:
            if self.technique_type == 'MockOCVTechnique':
                self.time = self._index * 0.1  # faster time step
                self.Ewe = 0.3 + 0.2 * np.sin(self._index * 0.1)  # use a sine wave
            elif self.technique_type == 'MockCPTechnique':
                self.time = self._index * 0.1
                self.Ewe = 0.2 * np.sin(self._index * 0.1)
            elif self.technique_type == 'MockPEISTechnique':
                self.Re_Z = 300 + 200 * np.sin(self._index * 0.1)
                self.Im_Z = -175 + 125 * np.sin(self._index * 0.1)
            elif self.technique_type == 'MockCVTechnique':
                self.Ewe = 0.5 * np.sin(self._index * 0.1)
                self.I = 0.001 * np.cos(self._index * 0.1)
            
            self.add_current_values_to_data()
            self._index += 1
            await asyncio.sleep(0.1)  # reduce the delay to 0.1 seconds
            yield self

@dataclass
class OCVParams:
    """simulated OCV parameters class"""
    rest_time_T: float = 60
    record_every_dT: float = 0.5
    record_every_dE: float = 10
    E_range: str = 'E_RANGE_2_5V'
    bandwidth: int = 5

@dataclass
class CPParams:
    """simulated CP parameters class"""
    record_every_dT: float = 0.1
    record_every_dE: float = 0.05
    n_cycles: int = 0
    steps: List[Any] = None
    I_range: str = 'I_RANGE_10mA'

@dataclass
class PEISParams:
    """simulated PEIS parameters class"""
    vs_initial: bool = False
    initial_voltage_step: float = 0.0
    duration_step: int = 60
    record_every_dT: float = 0.5
    record_every_dI: float = 0.01
    final_frequency: float = 1
    initial_frequency: float = 200000
    sweep: str = 'log'
    amplitude_voltage: float = 0.01
    frequency_number: int = 60
    average_n_times: int = 2
    correction: bool = False
    wait_for_steady: float = 0.1
    bandwidth: int = 5
    E_range: str = 'E_RANGE_2_5V'

@dataclass
class CVParams:
    """simulated CV parameters class"""
    record_every_dE: float = 0.01
    average_over_dE: bool = False
    n_cycles: int = 5
    begin_measuring_i: float = 0.5
    end_measuring_i: float = 1
    steps: List[Any] = None
    bandwidth: int = 5
    I_range: str = 'I_RANGE_100mA'

@dataclass
class CPStep:
    """simulated CP step class"""
    current: float
    duration: int
    vs_initial: bool = False

@dataclass
class CVStep:
    """simulated CV step class"""
    voltage: float
    scan_rate: float
    vs_initial: bool = False

class MockTechnique:
    """simulated electrochemical technique base class"""
    def __init__(self, params: Any):
        self.params = params
        self.tech_index = 0
        self.name = self.__class__.__name__
        
    async def generate_data(self) -> MockData:
        """generate simulated data"""
        raise NotImplementedError

class MockOCVTechnique(MockTechnique):
    """simulated OCV technique"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockOCVTechnique')
        async for d in data.generate_data():
            yield d

class MockCPTechnique(MockTechnique):
    """simulated CP technique"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockCPTechnique')
        async for d in data.generate_data():
            yield d

class MockPEISTechnique(MockTechnique):
    """simulated PEIS technique"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockPEISTechnique')
        async for d in data.generate_data():
            yield d

class MockCVTechnique(MockTechnique):
    """simulated CV technique"""
    async def generate_data(self) -> MockData:
        data = MockData(technique_type='MockCVTechnique')
        async for d in data.generate_data():
            yield d

class MockChannel:
    """simulated channel class"""
    def __init__(self):
        self.techniques = []
        self.current_tech_index = 0
        self.data = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)
    
    def run_techniques(self, techniques: List[MockTechnique]) -> Any:
        """run the technique sequence"""
        self.techniques = techniques
        return self
    
    async def __aiter__(self):
        """async iterator"""
        for i, tech in enumerate(self.techniques):
            tech.tech_index = i
            self.logger.info(f"starting to execute technique {tech.__class__.__name__} (index: {i})")
            async for data in tech.generate_data():
                yield MockResult(i, data)

    async def start_technique(self, technique):
        """start the technique test"""
        self.is_running = True
        self.logger.info(f"starting to execute technique {technique.__class__.__name__}")
        
        mock_data = MockData(technique_type=technique.__class__.__name__)
        self.logger.debug(f"creating a new MockData object, technique type: {mock_data.technique_type}")
        
        async for data in mock_data.generate_data():
            if not self.is_running:
                self.logger.info("technique execution was interrupted")
                break
                
            # ensure the technique type is correctly set
            data.technique_type = technique.__class__.__name__
            self.logger.debug(f"generating data point: {data.get_data_size()}")
            
            yield data
            await asyncio.sleep(0.1)
            
        self.logger.info("technique execution completed")
        self.is_running = False

    def stop(self):
        """stop the technique test"""
        self.logger.info("requesting to stop technique execution")
        self.is_running = False

class MockResult:
    """simulated result class"""
    def __init__(self, tech_index: int, data: MockData):
        self.tech_index = tech_index
        self.data = data

class MockBiologic:
    """simulated Biologic device class"""
    def __init__(self, port: str = 'USB0'):
        self.port = port
        self.connected = False
    
    def __enter__(self):
        self.connected = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connected = False
    
    def get_channel(self, channel_number: int) -> MockChannel:
        """get the channel"""
        if not self.connected:
            raise RuntimeError("device not connected")
        return MockChannel()

def connect(port: str = 'USB0') -> MockBiologic:
    """simulate the connection function"""
    return MockBiologic(port) 
