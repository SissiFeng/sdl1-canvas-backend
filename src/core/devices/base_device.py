"""
Base device interface for the automated electrochemical experiment system.
"""
from abc import ABC, abstractmethod
from typing import Optional
from src.utils.logging_utils import ExperimentLogger

class DeviceError(Exception):
    """Base exception for device-related errors"""
    pass

class ConnectionError(DeviceError):
    """Exception for device connection errors"""
    pass

class OperationError(DeviceError):
    """Exception for device operation errors"""
    pass

class BaseDevice(ABC):
    """Abstract base class for all device controllers"""
    
    def __init__(self, logger: Optional[ExperimentLogger] = None):
        self.logger = logger
        self.connected = False
        
    def log(self, level: str, message: str, **kwargs):
        """Log message if logger is available"""
        if self.logger:
            getattr(self.logger, level)(message, **kwargs)
            
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the device
        
        Returns
        -------
        bool
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the device
        
        Returns
        -------
        bool
            True if disconnection successful, False otherwise
        """
        pass
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
        
    @property
    def is_connected(self) -> bool:
        """Check if device is connected"""
        return self.connected 
