"""
Standalone test script for real-time visualization
"""

import os
import asyncio
import logging
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger("visualization_test")

class MockResult:
    def __init__(self):
        self._data = {
            'time': [],
            'Ewe': []
        }
    
    def add_data_point(self, time, voltage):
        self._data['time'].append(time)
        self._data['Ewe'].append(voltage)
        logger.debug(f"Added data point: time={time}, voltage={voltage}")
    
    def to_json(self):
        return self._data

class MockData:
    def __init__(self):
        self.data = MockResult()

    def add_point(self, time, voltage):
        self.data.add_data_point(time, voltage)
        return self

class SimpleVisualizer:
    def __init__(self):
        # Set up the plot
        plt.ion()  # Enable interactive mode
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.line, = self.ax.plot([], [], 'bo-', markersize=4, label='Voltage')
        
        # Configure plot
        self.ax.set_xlabel('Time (s)')
        self.ax.set_ylabel('Voltage (V)')
        self.ax.set_title('Real-time Data')
        self.ax.grid(True)
        self.ax.legend()
        
        # Initialize data storage
        self.times = []
        self.voltages = []
        
        # Show the plot
        plt.show(block=False)
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        
        logger.info("Visualizer initialized")

    async def update(self, data):
        try:
            if hasattr(data, 'data') and hasattr(data.data, 'to_json'):
                json_data = data.data.to_json()
                
                # Get the latest data point
                time = json_data['time'][-1]
                voltage = json_data['Ewe'][-1]
                
                # Add to our data lists
                self.times.append(time)
                self.voltages.append(voltage)
                
                # Update the line with all data
                self.line.set_data(self.times, self.voltages)
                
                # Adjust the plot limits
                self.ax.relim()
                self.ax.autoscale_view()
                
                # Redraw the plot
                self.figure.canvas.draw()
                self.figure.canvas.flush_events()
                
                logger.debug(f"Updated plot with point: t={time:.2f}, V={voltage:.4f}")
                
        except Exception as e:
            logger.error(f"Error updating plot: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

async def run_test():
    try:
        # Create visualizer
        viz = SimpleVisualizer()
        
        # Create mock data source
        mock_data = MockData()
        
        # Generate and plot data
        logger.info("Starting data generation...")
        for i in range(100):  # Generate 100 points
            # Create data point
            time = i * 0.1  # 100ms between points
            voltage = 0.5 + 0.2 * np.sin(time) + 0.05 * np.random.randn()
            
            # Add to mock data
            mock_data.add_point(time, voltage)
            
            # Update plot
            await viz.update(mock_data)
            
            # Small delay to simulate real-time data
            await asyncio.sleep(0.1)
        
        logger.info("Data generation complete")
        input("Press Enter to exit...")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise
    finally:
        plt.close('all')

if __name__ == "__main__":
    logger.info("Starting visualization test...")
    asyncio.run(run_test()) 
