"""
Logging utilities for the automated electrochemical experiment system.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional

class ExperimentLogger:
    """Centralized logging for experiment operations"""
    
    def __init__(self, experiment_id: str, log_dir: str):
        self.experiment_id = experiment_id
        self.logger = self._setup_logger(log_dir)
        
    def _setup_logger(self, log_dir: str) -> logging.Logger:
        """Setup logging configuration"""
        # Create logger
        logger = logging.getLogger(self.experiment_id)
        logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
        
        # Create file handler
        log_file = os.path.join(log_dir, f"{self.experiment_id}.log")
        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setFormatter(formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        self._log(logging.INFO, message, **kwargs)
        
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        self._log(logging.DEBUG, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        self._log(logging.WARNING, message, **kwargs)
        
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error level message"""
        if error:
            message = f"{message}: {str(error)}"
        self._log(logging.ERROR, message, **kwargs)
        
    def _log(self, level: int, message: str, **kwargs):
        """Internal method to handle logging with additional context"""
        if kwargs:
            context = " ".join([f"{k}={v}" for k, v in kwargs.items()])
            message = f"{message} [{context}]"
        self.logger.log(level, message) 
