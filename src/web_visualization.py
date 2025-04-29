"""
Web-based real-time visualization for Biologic data
"""

import os
import sys
import asyncio
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import project modules
from src.utils.websocket_server import WebSocketServer
from src.utils.websocket_handler import WebSocketDataHandler
from src.utils.data_processing import create_experiment_config, ExperimentController

# Import Biologic modules
try:
    from biologic import connect
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Web-based real-time visualization for Biologic data")
    
    parser.add_argument("--biologic-port", default="USB0", help="Biologic USB port (default: USB0)")
    parser.add_argument("--channel", type=int, default=1, help="Biologic channel (default: 1)")
    parser.add_argument("--host", default="0.0.0.0", help="WebSocket server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port (default: 8765)")
    parser.add_argument("--technique", default="cv", choices=["ocv", "cv", "peis", "cp", "lp"], 
                        help="Technique to run (default: cv)")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of real device")
    
    return parser.parse_args()

def create_techniques(technique_name):
    """Create technique objects based on technique name"""
    if technique_name == "ocv":
        # Open Circuit Voltage technique
        ocv_params = OCVParams(
            rest_time=60,  # 60 seconds
            record_every_dt=0.1  # Record every 0.1 seconds
        )
        return [OCVTechnique(ocv_params)]
    
    elif technique_name == "cv":
        # Cyclic Voltammetry technique
        cv_steps = [
            CVStep(
                vs_initial=False,
                voltage_step=0.5,  # 0.5V
                scan_rate=0.05,  # 50mV/s
                n_cycles=3
            )
        ]
        cv_params = CVParams(
            steps=cv_steps,
            n_cycles=3,
            record_every_dE=0.001  # Record every 1mV
        )
        return [CVTechnique(cv_params)]
    
    elif technique_name == "peis":
        # Electrochemical Impedance Spectroscopy technique
        peis_params = PEISParams(
            vs_initial=False,
            initial_voltage_step=0.0,
            final_frequency=0.1,  # 0.1Hz
            initial_frequency=100000,  # 100kHz
            sweep=SweepMode.Logarithmic,
            amplitude_voltage=0.01,  # 10mV
            frequency_number=50
        )
        return [PEISTechnique(peis_params)]
    
    elif technique_name == "cp":
        # Chronopotentiometry technique
        cp_steps = [
            CPStep(
                current=0.001,  # 1mA
                duration=30,  # 30 seconds
                vs_initial=False
            )
        ]
        cp_params = CPParams(
            steps=cp_steps,
            record_every_dt=0.1  # Record every 0.1 seconds
        )
        return [CPTechnique(cp_params)]
    
    elif technique_name == "lp":
        # Linear Polarization technique
        lp_steps = [
            LPStep(
                vs_initial=True,
                voltage_step=-0.01,  # -10mV
                scan_rate=0.001,  # 1mV/s
                n_cycles=1
            ),
            LPStep(
                vs_initial=True,
                voltage_step=0.01,  # +10mV
                scan_rate=0.001,  # 1mV/s
                n_cycles=1
            )
        ]
        lp_params = LPParams(
            steps=lp_steps,
            record_every_dE=0.0001  # Record every 0.1mV
        )
        return [LPTechnique(lp_params)]
    
    else:
        raise ValueError(f"Unknown technique: {technique_name}")

async def run_visualization(args):
    """Run web-based visualization"""
    try:
        # Create experiment ID and paths
        experiment_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_web_viz"
        experiment_path = os.path.join(os.getcwd(), 'data', experiment_id)
        
        # Create experiment configuration
        config = create_experiment_config(experiment_id, experiment_path)
        
        # Create WebSocket server
        web_dir = os.path.join(os.path.dirname(__file__), 'web')
        server = WebSocketServer(host=args.host, port=args.port, static_dir=web_dir)
        
        # Start WebSocket server
        await server.start()
        logger.info(f"WebSocket server started at http://{args.host}:{args.port}")
        
        # Create experiment controller
        controller = ExperimentController(config)
        
        # Create WebSocket data handler
        ws_handler = WebSocketDataHandler(server)
        
        # Create techniques
        techniques = create_techniques(args.technique)
        
        if args.mock:
            # Use mock data
            logger.info("Using mock data instead of real device")
            from src.core.devices.mock_biologic_device import MockChannel
            channel = MockChannel()
            controller.initialize(channel)
            
            # Add WebSocket handler
            controller.data_acquisition.add_handler(ws_handler)
            
            # Run experiment
            logger.info(f"Starting mock experiment with technique: {args.technique}")
            await controller.run_experiment(techniques)
        else:
            # Use real device
            logger.info(f"Connecting to Biologic on {args.biologic_port}")
            with connect(args.biologic_port) as bl:
                channel = bl.get_channel(args.channel)
                controller.initialize(channel)
                
                # Add WebSocket handler
                controller.data_acquisition.add_handler(ws_handler)
                
                # Run experiment
                logger.info(f"Starting experiment with technique: {args.technique}")
                await controller.run_experiment(techniques)
        
        # Keep server running
        logger.info("Experiment completed. Server still running. Press Ctrl+C to exit.")
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error running visualization: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Stop WebSocket server
        if 'server' in locals():
            await server.stop()
        logger.info("Server stopped")

async def main():
    """Main function"""
    args = parse_arguments()
    
    # Override mock flag if USE_MOCK is True
    if USE_MOCK:
        args.mock = True
        logger.warning("Biologic library not found. Using mock data.")
    
    await run_visualization(args)

if __name__ == "__main__":
    asyncio.run(main())
