"""
automatic electrochemical experiment system main program
"""

import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import sys
import logging
import asyncio
import argparse
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# add project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# choose to use real device or mock device based on environment
try:
    from biologic import connect, BANDWIDTH, I_RANGE, E_RANGE
    from biologic.techniques.ocv import OCVTechnique, OCVParams
    from biologic.techniques.peis import PEISTechnique, PEISParams, SweepMode
    from biologic.techniques.cv import CVTechnique, CVParams, CVStep
    from biologic.techniques.cp import CPTechnique, CPParams, CPStep
    from biologic.techniques.lp import LPTechnique, LPParams, LPStep
    USE_MOCK = False
except ImportError:
    from src.core.devices.mock_biologic_device import (
        connect, MockOCVTechnique as OCVTechnique,
        MockPEISTechnique as PEISTechnique,
        MockCVTechnique as CVTechnique,
        MockCPTechnique as CPTechnique,
        OCVParams, PEISParams, CVParams, CPParams,
        CVStep, CPStep
    )
    USE_MOCK = True
    # define constants for mock device
    class BANDWIDTH:
        BW_5 = 5
    class I_RANGE:
        I_RANGE_10mA = '10mA'
        I_RANGE_100mA = '100mA'
    class E_RANGE:
        E_RANGE_2_5V = '2.5V'
        E_RANGE_10V = '10V'
    class SweepMode:
        Logarithmic = 'log'

from src.core.devices.opentrons_device import OpentronsDevice
from src.core.devices.arduino_device import ArduinoDevice
from src.utils.data_processing import create_experiment_config, ExperimentController
from src.utils.config_loader import ConfigLoader, ExperimentParams

def setup_logging(experiment_id: str) -> None:
    """setup logging system"""
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{experiment_id}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def parse_arguments() -> argparse.Namespace:
    """parse command line arguments"""
    parser = argparse.ArgumentParser(description="automatic electrochemical experiment system")
    
    # parameter source selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--params-file", help="parameter configuration file path (CSV or Excel)")
    group.add_argument("--generate-template", help="generate parameter template file")
    group.add_argument("--single-run", action="store_true", help="single run mode")
    
    # parameters for single run mode
    single_run_group = parser.add_argument_group("single run parameters")
    single_run_group.add_argument("--run-number", help="experiment run number")
    single_run_group.add_argument("--well", help="well to test (e.g., 'C5')")
    single_run_group.add_argument("--experiment-type", 
                                choices=['deposition', 'characterization', 'full'],
                                help="experiment type")
    single_run_group.add_argument("--robot-ip", default="100.67.89.154",
                                help="OT2 robot IP address")
    single_run_group.add_argument("--arduino-port", help="Arduino device port")
    single_run_group.add_argument("--biologic-port", default="USB0",
                                help="Biologic device USB port")
    single_run_group.add_argument("--deposition-current", type=float,
                                default=-0.002, help="deposition current (A)")
    single_run_group.add_argument("--deposition-duration", type=int,
                                default=60, help="deposition time (s)")
    
    args = parser.parse_args()
    
    # validate required parameters for single run mode
    if args.single_run:
        if not all([args.run_number, args.well, args.experiment_type]):
            parser.error("single run mode requires --run-number, --well and --experiment-type")
    
    return args

def create_deposition_techniques(params: ExperimentParams) -> list:
    """create deposition experiment techniques sequence"""
    # OCV technique
    ocv_params = OCVParams(
        rest_time_T=60,
        record_every_dT=0.5,
        record_every_dE=10,
        E_range=E_RANGE.E_RANGE_2_5V,
        bandwidth=BANDWIDTH.BW_5
    )
    ocv_tech = OCVTechnique(ocv_params)
    
    # CP technique
    cp_step = CPStep(
        current=params.deposition_current,
        duration=params.deposition_duration,
        vs_initial=False
    )
    cp_params = CPParams(
        record_every_dT=0.1,
        record_every_dE=0.05,
        n_cycles=0,
        steps=[cp_step],
        I_range=I_RANGE.I_RANGE_10mA
    )
    cp_tech = CPTechnique(cp_params)
    
    return [ocv_tech, cp_tech, ocv_tech]

def create_characterization_techniques() -> list:
    """create characterization experiment techniques sequence"""
    techniques = []
    
    # OCV
    ocv_params = OCVParams(
        rest_time_T=10,
        record_every_dT=0.5,
        record_every_dE=10,
        E_range=E_RANGE.E_RANGE_10V,
        bandwidth=BANDWIDTH.BW_5
    )
    techniques.append(OCVTechnique(ocv_params))
    
    # PEIS
    peis_params = PEISParams(
        vs_initial=False,
        initial_voltage_step=0.0,
        duration_step=60,
        record_every_dT=0.5,
        record_every_dI=0.01,
        final_frequency=1,
        initial_frequency=200000,
        sweep=SweepMode.Logarithmic,
        amplitude_voltage=0.01,
        frequency_number=60,
        average_n_times=2,
        correction=False,
        wait_for_steady=0.1,
        bandwidth=BANDWIDTH.BW_5,
        E_range=E_RANGE.E_RANGE_2_5V
    )
    techniques.append(PEISTechnique(peis_params))
    
    # CV
    cv_steps = [
        CVStep(voltage=0, scan_rate=0.05, vs_initial=False),
        CVStep(voltage=1, scan_rate=0.05, vs_initial=False),
        CVStep(voltage=0, scan_rate=0.05, vs_initial=False)
    ]
    cv_params = CVParams(
        record_every_dE=0.01,
        average_over_dE=False,
        n_cycles=5,
        begin_measuring_i=0.5,
        end_measuring_i=1,
        steps=cv_steps,
        bandwidth=BANDWIDTH.BW_5,
        I_range=I_RANGE.I_RANGE_100mA
    )
    techniques.append(CVTechnique(cv_params))
    
    return techniques

async def run_experiment(params: ExperimentParams) -> None:
    """run a single experiment"""
    # create experiment ID and path
    experiment_id = f"{datetime.now().strftime('%Y%m%d')}_{params.run_number}"
    experiment_path = os.path.join(os.getcwd(), 'data', experiment_id)
    
    # setup logging
    setup_logging(experiment_id)
    logger = logging.getLogger(__name__)
    logger.info(f"Starting experiment {experiment_id}")
    
    # create experiment configuration and controller
    config = create_experiment_config(experiment_id, experiment_path)
    controller = ExperimentController(config)
    
    try:
        # initialize devices
        opentrons = OpentronsDevice(params.robot_ip)
        arduino = ArduinoDevice(params.arduino_port)
        
        # connect devices
        await opentrons.connect()
        await arduino.connect()
        
        # prepare experiment techniques
        if params.experiment_type in ['deposition', 'full']:
            deposition_techniques = create_deposition_techniques(params)
        if params.experiment_type in ['characterization', 'full']:
            characterization_techniques = create_characterization_techniques()
        
        # run experiment
        with connect(params.biologic_port) as bl:
            channel = bl.get_channel(1)
            controller.initialize(channel)
            
            if params.experiment_type in ['deposition', 'full']:
                logger.info("Starting deposition experiment")
                await controller.run_experiment(deposition_techniques)
            
            if params.experiment_type in ['characterization', 'full']:
                logger.info("Starting characterization experiment")
                await controller.run_experiment(characterization_techniques)
        
        logger.info(f"Experiment {experiment_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Experiment failed: {str(e)}")
        raise
    finally:
        # clean up device connections
        await opentrons.disconnect()
        await arduino.disconnect()

async def main():
    """main program"""
    args = parse_arguments()
    config_loader = ConfigLoader()
    
    # generate template file
    if args.generate_template:
        config_loader.save_template(args.generate_template)
        print(f"parameter template file generated: {args.generate_template}")
        return
    
    # load parameters from file
    if args.params_file:
        if args.params_file.endswith('.csv'):
            params_list = config_loader.load_from_csv(args.params_file)
        elif args.params_file.endswith(('.xlsx', '.xls')):
            params_list = config_loader.load_from_excel(args.params_file)
        else:
            raise ValueError("unsupported file format, please use CSV or Excel file")
        
        # run experiments in batch
        for params in params_list:
            await run_experiment(params)
    
    # single run mode
    elif args.single_run:
        params = ExperimentParams(
            run_number=args.run_number,
            well=args.well,
            experiment_type=args.experiment_type,
            robot_ip=args.robot_ip,
            arduino_port=args.arduino_port,
            biologic_port=args.biologic_port,
            deposition_current=args.deposition_current,
            deposition_duration=args.deposition_duration
        )
        await run_experiment(params)

if __name__ == "__main__":
    asyncio.run(main()) 
