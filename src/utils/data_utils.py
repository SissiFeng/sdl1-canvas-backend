"""
Data handling utilities for the automated electrochemical experiment system.
"""
import os
import json
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

class ExperimentDataManager:
    """Manages experiment data storage and retrieval"""
    
    def __init__(self, experiment_id: str, base_dir: str):
        self.experiment_id = experiment_id
        self.base_dir = base_dir
        
    def save_technique_data(self, 
                          data: pd.DataFrame,
                          technique_id: int,
                          technique_name: str,
                          data_type: str = "characterization") -> str:
        """
        Save technique data to CSV file
        
        Parameters
        ----------
        data : pd.DataFrame
            Data to save
        technique_id : int
            Technique identifier
        technique_name : str
            Name of the technique
        data_type : str
            Type of data (characterization or deposition)
            
        Returns
        -------
        str
            Path to saved file
        """
        filename = f"{self.experiment_id}_{technique_id}_{technique_name}.csv"
        save_dir = os.path.join(self.base_dir, data_type)
        filepath = os.path.join(save_dir, filename)
        
        data.to_csv(filepath, index=False)
        return filepath
    
    def save_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Save experiment metadata to JSON file
        
        Parameters
        ----------
        metadata : Dict[str, Any]
            Metadata to save
            
        Returns
        -------
        str
            Path to saved file
        """
        filename = "metadata.json"
        filepath = os.path.join(self.base_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        return filepath
    
    def update_metadata(self, updates: Dict[str, Any]) -> None:
        """
        Update existing metadata file
        
        Parameters
        ----------
        updates : Dict[str, Any]
            New metadata values to update
        """
        filepath = os.path.join(self.base_dir, "metadata.json")
        
        # Read existing metadata
        with open(filepath, 'r') as f:
            metadata = json.load(f)
        
        # Update metadata
        metadata.update(updates)
        
        # Save updated metadata
        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=4)
    
    def load_technique_data(self, 
                          technique_id: int,
                          technique_name: str,
                          data_type: str = "characterization") -> Optional[pd.DataFrame]:
        """
        Load technique data from CSV file
        
        Parameters
        ----------
        technique_id : int
            Technique identifier
        technique_name : str
            Name of the technique
        data_type : str
            Type of data (characterization or deposition)
            
        Returns
        -------
        Optional[pd.DataFrame]
            Loaded data or None if file doesn't exist
        """
        filename = f"{self.experiment_id}_{technique_id}_{technique_name}.csv"
        filepath = os.path.join(self.base_dir, data_type, filename)
        
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        return None
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Load experiment metadata
        
        Returns
        -------
        Optional[Dict[str, Any]]
            Metadata or None if file doesn't exist
        """
        filepath = os.path.join(self.base_dir, "metadata.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return None 
