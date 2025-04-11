"""
workflow test module, used to verify the complete workflow of the automated experiment system
including the test of electroplating and characterization experiments
"""
import os
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd
from collections import defaultdict

from core.devices.mock_biologic_device import (
    MockData, MockOCVTechnique, MockCPTechnique, 
    MockPEISTechnique, MockCVTechnique,
    OCVParams, CPParams, PEISParams, CVParams,
    CPStep, CVStep
)
from utils.config_loader import ExperimentParams
from utils.data_processing import ExperimentDataManager

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """test configuration"""
    experiment_id: str
    base_dir: str = "test_data"
    deposition_current: float = -0.002  # deposition current (A)
    deposition_duration: float = 60     # deposition time (s)
    well_to_test: str = "C5"           # well to test

class MockBiologicDevice:
    """mock Biologic device"""
    def __init__(self, data_manager: ExperimentDataManager):
        self.data_manager = data_manager
        self.connected = False
        
    def connect(self) -> bool:
        """connect to the device"""
        self.connected = True
        logger.info("Connected to mock Biologic device")
        return True
        
    def disconnect(self) -> bool:
        """disconnect from the device"""
        self.connected = False
        logger.info("Disconnected from mock Biologic device")
        return True
        
    async def run_techniques(self, techniques: List[Any], data_type: str = "characterization") -> None:
        """run electrochemical technique sequence"""
        if not self.connected:
            raise ConnectionError("Not connected to mock Biologic device")
            
        for tech_id, technique in enumerate(techniques):
            logger.info(f"Running technique {tech_id}: {type(technique).__name__}")
            
            # generate simulated data
            data_points = defaultdict(list)
            async for point in technique.generate_data():
                # get data from MockData object
                data = point.to_json()
                for key, values in data.items():
                    if values:  # only add non-empty latest data points
                        data_points[key].append(values[-1])
            
            # convert data points to DataFrame
            df = pd.DataFrame(data_points)
            
            # save data
            self.data_manager.save_technique_data(
                data=df,
                technique_id=tech_id,
                technique_name=type(technique).__name__,
                data_type=data_type
            )
            
class WorkflowTester:
    """workflow tester"""
    def __init__(self, config: TestConfig):
        self.config = config
        self.data_manager = ExperimentDataManager(
            experiment_id=config.experiment_id,
            base_dir=config.base_dir
        )
        self.device = MockBiologicDevice(self.data_manager)
        
    def setup(self) -> None:
        """set up test environment"""
        # create data directory
        os.makedirs(os.path.join(self.config.base_dir, "deposition"), exist_ok=True)
        os.makedirs(os.path.join(self.config.base_dir, "characterization"), exist_ok=True)
        
        # save metadata
        metadata = {
            "date": datetime.now().strftime("%Y%m%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "experimentID": self.config.experiment_id,
            "cell": self.config.well_to_test,
            "status": "testing",
            "type": "workflow_test"
        }
        self.data_manager.save_metadata(metadata)
        
    async def test_deposition_workflow(self) -> None:
        """test deposition workflow"""
        logger.info("Testing deposition workflow...")
        
        try:
            # connect to the device
            self.device.connect()
            
            # create deposition technique sequence
            techniques = []
            
            # add OCV technique
            ocv_params = OCVParams(
                rest_time_T=60,
                record_every_dT=0.5,
                record_every_dE=10
            )
            techniques.append(MockOCVTechnique(ocv_params))
            
            # add CP technique
            cp_step = CPStep(
                current=self.config.deposition_current,
                duration=self.config.deposition_duration
            )
            cp_params = CPParams(
                record_every_dT=0.1,
                record_every_dE=0.05,
                steps=[cp_step]
            )
            techniques.append(MockCPTechnique(cp_params))
            
            # add final OCV technique
            techniques.append(MockOCVTechnique(ocv_params))
            
            # run technique sequence
            await self.device.run_techniques(techniques, "deposition")
            
            logger.info("Deposition workflow test completed successfully")
            
        except Exception as e:
            logger.error(f"Error in deposition workflow test: {str(e)}")
            raise
            
        finally:
            self.device.disconnect()
            
    async def test_characterization_workflow(self) -> None:
        """test characterization workflow"""
        logger.info("Testing characterization workflow...")
        
        try:
            # connect to the device
            self.device.connect()
            
            # create characterization technique sequence
            techniques = []
            
            # add initial OCV
            ocv_params = OCVParams(
                rest_time_T=10,
                record_every_dT=0.5
            )
            techniques.append(MockOCVTechnique(ocv_params))
            
            # add CV techniques with different scan rates
            for scan_rate in [0.02, 0.04, 0.06, 0.08, 0.1]:
                cv_steps = [
                    CVStep(voltage=-0.2, scan_rate=scan_rate, vs_initial=False),
                    CVStep(voltage=1.0, scan_rate=scan_rate, vs_initial=False),
                    CVStep(voltage=-0.2, scan_rate=scan_rate, vs_initial=False)
                ]
                cv_params = CVParams(
                    record_every_dE=0.01,
                    n_cycles=3,
                    steps=cv_steps
                )
                techniques.append(MockCVTechnique(cv_params))
                
            # add PEIS technique
            peis_params_list = [
                PEISParams(
                    initial_voltage_step=0.0,
                    final_frequency=0.1,
                    initial_frequency=200000,
                    amplitude_voltage=0.01
                ),
                PEISParams(
                    initial_voltage_step=1.0,
                    final_frequency=0.1,
                    initial_frequency=200000,
                    amplitude_voltage=0.01
                )
            ]
            for params in peis_params_list:
                techniques.append(MockPEISTechnique(params))
            
            # add activity and stability tests
            cv_steps_activity = [
                CVStep(voltage=0.0, scan_rate=0.05, vs_initial=False),
                CVStep(voltage=1.0, scan_rate=0.05, vs_initial=False),
                CVStep(voltage=0.0, scan_rate=0.05, vs_initial=False)
            ]
            cv_params_activity = CVParams(
                record_every_dE=0.01,
                n_cycles=5,
                steps=cv_steps_activity
            )
            techniques.append(MockCVTechnique(cv_params_activity))
            
            cv_steps_stability = [
                CVStep(voltage=0.0, scan_rate=0.1, vs_initial=False),
                CVStep(voltage=1.0, scan_rate=0.1, vs_initial=False),
                CVStep(voltage=0.0, scan_rate=0.1, vs_initial=False)
            ]
            cv_params_stability = CVParams(
                record_every_dE=0.01,
                n_cycles=1000,
                steps=cv_steps_stability
            )
            techniques.append(MockCVTechnique(cv_params_stability))
            
            # run technique sequence
            await self.device.run_techniques(techniques, "characterization")
            
            logger.info("Characterization workflow test completed successfully")
            
        except Exception as e:
            logger.error(f"Error in characterization workflow test: {str(e)}")
            raise
            
        finally:
            self.device.disconnect()
            
    async def run_all_tests(self) -> None:
        """run all tests"""
        try:
            self.setup()
            await self.test_deposition_workflow()
            await self.test_characterization_workflow()
            
            # update test status
            self.data_manager.update_metadata({
                "status": "completed",
                "completion_time": datetime.now().strftime("%H:%M:%S")
            })
            
            logger.info("All workflow tests completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow tests failed: {str(e)}")
            self.data_manager.update_metadata({
                "status": "failed",
                "error": str(e)
            })
            raise

async def main():
    """main function"""
    # create test configuration
    config = TestConfig(
        experiment_id=f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    # create workflow tester
    tester = WorkflowTester(config)
    
    # run tests
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 
