"""
configuration loader module, for loading experiment parameters from different sources (command line, CSV, Excel, etc.)
"""

import pandas as pd
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import os
import logging
from datetime import datetime

@dataclass
class ExperimentParams:
    """experiment parameters data class"""
    run_number: str
    well: str
    experiment_type: str
    robot_ip: str = "100.67.89.154"
    arduino_port: Optional[str] = None
    biologic_port: str = "USB0"
    deposition_current: float = -0.002
    deposition_duration: int = 60

class ConfigLoader:
    """configuration loader class"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def load_from_csv(self, file_path: str) -> List[ExperimentParams]:
        """load experiment parameters from CSV file"""
        try:
            df = pd.read_csv(file_path)
            return self._process_dataframe(df)
        except Exception as e:
            self.logger.error(f"从CSV加载参数失败: {str(e)}")
            raise

    def load_from_excel(self, file_path: str, sheet_name: Optional[str] = None) -> List[ExperimentParams]:
        """load experiment parameters from Excel file"""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return self._process_dataframe(df)
        except Exception as e:
            self.logger.error(f"从Excel加载参数失败: {str(e)}")
            raise

    def _process_dataframe(self, df: pd.DataFrame) -> List[ExperimentParams]:
        """process the dataframe and convert to parameter list"""
        required_columns = ['run_number', 'well', 'experiment_type']
        
        # check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"missing required columns: {', '.join(missing_columns)}")

        # validate the values of experiment_type
        valid_types = ['deposition', 'characterization', 'full']
        invalid_types = df[~df['experiment_type'].isin(valid_types)]['experiment_type'].unique()
        if len(invalid_types) > 0:
            raise ValueError(f"invalid experiment types: {invalid_types}")

        params_list = []
        for _, row in df.iterrows():
            params = ExperimentParams(
                run_number=str(row['run_number']),
                well=str(row['well']),
                experiment_type=str(row['experiment_type']),
                robot_ip=str(row.get('robot_ip', "100.67.89.154")),
                arduino_port=str(row['arduino_port']) if 'arduino_port' in row else None,
                biologic_port=str(row.get('biologic_port', "USB0")),
                deposition_current=float(row.get('deposition_current', -0.002)),
                deposition_duration=int(row.get('deposition_duration', 60))
            )
            params_list.append(params)

        return params_list

    def save_template(self, file_path: str, format: str = 'csv') -> None:
        """save the parameter template file"""
        template_data = {
            'run_number': ['001', '002'],
            'well': ['C5', 'C6'],
            'experiment_type': ['full', 'deposition'],
            'robot_ip': ['100.67.89.154', '100.67.89.154'],
            'arduino_port': [None, None],
            'biologic_port': ['USB0', 'USB0'],
            'deposition_current': [-0.002, -0.003],
            'deposition_duration': [60, 90]
        }
        
        df = pd.DataFrame(template_data)
        
        if format.lower() == 'csv':
            df.to_csv(file_path, index=False)
        elif format.lower() == 'excel':
            df.to_excel(file_path, index=False)
        else:
            raise ValueError("不支持的文件格式，请使用 'csv' 或 'excel'")

        self.logger.info(f"模板文件已保存到: {file_path}")

def validate_experiment_params(params: ExperimentParams) -> None:
    """validate the experiment parameters"""
    if not params.run_number:
        raise ValueError("run number cannot be empty")
    
    if not params.well:
        raise ValueError("well cannot be empty")
    
    if params.experiment_type not in ['deposition', 'characterization', 'full']:
        raise ValueError(f"invalid experiment type: {params.experiment_type}")
    
    if params.deposition_current >= 0:
        raise ValueError("deposition current must be negative")
    
    if params.deposition_duration <= 0:
        raise ValueError("deposition duration must be greater than 0")
