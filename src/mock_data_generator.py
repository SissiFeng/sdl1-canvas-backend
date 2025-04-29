"""
Mock data generator for testing WebSocket server and frontend visualization
"""

import os
import sys
import asyncio
import logging
import argparse
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import project modules
from src.utils.websocket_server import WebSocketServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class MockData:
    """Mock data class for different electrochemical techniques"""
    technique_type: str
    data: Dict[str, List[float]] = field(default_factory=dict)
    
    def to_json(self) -> Dict[str, List[float]]:
        """Convert data to JSON format"""
        return self.data

@dataclass
class MockDataPoint:
    """Mock data point class"""
    data: MockData
    tech_index: int = 0

def generate_cv_data(num_points: int = 100, cycles: int = 3):
    """Generate Cyclic Voltammetry data"""
    # Create voltage sweep (triangular wave)
    voltage_min = -0.5
    voltage_max = 0.5
    
    points_per_cycle = num_points // cycles
    voltages = []
    
    for _ in range(cycles):
        # Forward sweep
        voltages.extend(np.linspace(voltage_min, voltage_max, points_per_cycle // 2))
        # Backward sweep
        voltages.extend(np.linspace(voltage_max, voltage_min, points_per_cycle // 2))
    
    # Add some noise to make it look realistic
    voltages = np.array(voltages)
    
    # Calculate current (I = sin(V) + noise)
    currents = 0.001 * np.sin(10 * voltages) + 0.0001 * np.random.randn(len(voltages))
    
    # Create mock data
    mock_data = MockData(technique_type="CV")
    mock_data.data = {
        'Ewe': voltages.tolist(),
        'I': currents.tolist()
    }
    
    return mock_data

def generate_ocv_data(num_points: int = 100, duration: int = 60):
    """Generate Open Circuit Voltage data"""
    # Create time array
    times = np.linspace(0, duration, num_points)
    
    # Create voltage array (exponential decay + noise)
    voltages = 0.5 * np.exp(-times / 20) + 0.2 + 0.01 * np.random.randn(num_points)
    
    # Create mock data
    mock_data = MockData(technique_type="OCV")
    mock_data.data = {
        'time': times.tolist(),
        'Ewe': voltages.tolist()
    }
    
    return mock_data

def generate_peis_data(num_points: int = 50):
    """Generate Electrochemical Impedance Spectroscopy data"""
    # Create frequency array (logarithmic)
    frequencies = np.logspace(5, -1, num_points)  # 100kHz to 0.1Hz
    
    # Create impedance components (simplified Randles circuit)
    R_s = 50  # Solution resistance (ohms)
    R_ct = 200  # Charge transfer resistance (ohms)
    C_dl = 1e-6  # Double layer capacitance (F)
    
    # Calculate impedance
    omega = 2 * np.pi * frequencies
    Z_c = 1 / (1j * omega * C_dl)
    Z = R_s + (R_ct * Z_c) / (R_ct + Z_c)
    
    # Extract real and imaginary parts
    Z_real = Z.real + 5 * np.random.randn(num_points)
    Z_imag = Z.imag + 5 * np.random.randn(num_points)
    
    # Create mock data
    mock_data = MockData(technique_type="PEIS")
    mock_data.data = {
        'freq': frequencies.tolist(),
        'Re(Z)': Z_real.tolist(),
        'Im(Z)': Z_imag.tolist()
    }
    
    return mock_data

def generate_cp_data(num_points: int = 100, duration: int = 30):
    """Generate Chronopotentiometry data"""
    # Create time array
    times = np.linspace(0, duration, num_points)
    
    # Create voltage array (logarithmic rise + noise)
    voltages = 0.2 * np.log(1 + times) + 0.3 + 0.01 * np.random.randn(num_points)
    
    # Create mock data
    mock_data = MockData(technique_type="CP")
    mock_data.data = {
        'time': times.tolist(),
        'Ewe': voltages.tolist()
    }
    
    return mock_data

def generate_lp_data(num_points: int = 100):
    """Generate Linear Polarization data"""
    # Create voltage array
    voltages = np.linspace(-0.01, 0.01, num_points)
    
    # Create current array (linear + noise)
    currents = 0.001 * voltages + 0.00001 * np.random.randn(num_points)
    
    # Create mock data
    mock_data = MockData(technique_type="LP")
    mock_data.data = {
        'Ewe': voltages.tolist(),
        'I': currents.tolist()
    }
    
    return mock_data

async def generate_and_send_data(server: WebSocketServer, technique: str, delay: float = 0.1):
    """Generate and send mock data to WebSocket clients"""
    # Generate mock data based on technique
    if technique == "cv":
        mock_data = generate_cv_data()
    elif technique == "ocv":
        mock_data = generate_ocv_data()
    elif technique == "peis":
        mock_data = generate_peis_data()
    elif technique == "cp":
        mock_data = generate_cp_data()
    elif technique == "lp":
        mock_data = generate_lp_data()
    else:
        raise ValueError(f"Unknown technique: {technique}")
    
    # Send technique change notification
    await server.broadcast({
        'type': 'technique_change',
        'technique': mock_data.technique_type
    })
    
    # Get data arrays
    if mock_data.technique_type in ["CV", "LP"]:
        x_data = mock_data.data['Ewe']
        y_data = mock_data.data['I']
    elif mock_data.technique_type == "PEIS":
        x_data = mock_data.data['Re(Z)']
        y_data = [-im for im in mock_data.data['Im(Z)']]
    else:  # OCV, CP
        x_data = mock_data.data['time']
        y_data = mock_data.data['Ewe']
    
    # Send data points one by one
    for i in range(len(x_data)):
        await server.broadcast({
            'type': 'data_point',
            'technique': mock_data.technique_type,
            'x': x_data[i],
            'y': y_data[i]
        })
        
        # Log progress
        if i % 10 == 0:
            logger.info(f"Sent {i}/{len(x_data)} data points")
        
        # Delay between points
        await asyncio.sleep(delay)
    
    logger.info(f"Finished sending {len(x_data)} data points")

async def run_mock_server(args):
    """Run mock data server"""
    try:
        # Create WebSocket server
        web_dir = os.path.join(os.path.dirname(__file__), 'web')
        server = WebSocketServer(host=args.host, port=args.port, static_dir=web_dir)
        
        # Start WebSocket server
        await server.start()
        logger.info(f"WebSocket server started at http://{args.host}:{args.port}")
        
        # Wait for clients to connect
        logger.info("Waiting for clients to connect...")
        await asyncio.sleep(2)
        
        # Generate and send data
        while True:
            logger.info(f"Generating {args.technique} data...")
            await generate_and_send_data(server, args.technique, args.delay)
            
            # Wait between data sets
            logger.info(f"Waiting {args.interval} seconds before next data set...")
            await asyncio.sleep(args.interval)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Error running mock server: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Stop WebSocket server
        if 'server' in locals():
            await server.stop()
        logger.info("Server stopped")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Mock data generator for WebSocket visualization")
    
    parser.add_argument("--host", default="0.0.0.0", help="WebSocket server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8765, help="WebSocket server port (default: 8765)")
    parser.add_argument("--technique", default="cv", choices=["ocv", "cv", "peis", "cp", "lp"], 
                        help="Technique to simulate (default: cv)")
    parser.add_argument("--delay", type=float, default=0.1, 
                        help="Delay between data points in seconds (default: 0.1)")
    parser.add_argument("--interval", type=int, default=5, 
                        help="Interval between data sets in seconds (default: 5)")
    
    return parser.parse_args()

async def main():
    """Main function"""
    args = parse_arguments()
    await run_mock_server(args)

if __name__ == "__main__":
    asyncio.run(main())
