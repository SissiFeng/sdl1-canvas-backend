"""
realtime data display test module
"""

import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'

import asyncio
import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@dataclass
class TestData:
    """test data class"""
    time: Optional[float] = None
    value: Optional[float] = None
    technique_type: str = 'TestTechnique'
    _data: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    def add_point(self, time: float, value: float):
        """add data point"""
        self.time = time
        self.value = value
        self._data['time'].append(time)
        self._data['value'].append(value)
        logger.debug(f"adding data point: time={time}, value={value}")

    def to_json(self) -> Dict[str, List[float]]:
        """convert to JSON format"""
        return {k: list(v) for k, v in self._data.items()}

class SimpleVisualizer:
    """simple realtime visualizer"""
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')
        self.data_x = []
        self.data_y = []
        
        # set chart
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_title('realtime data display test')
        self.ax.set_xlabel('time (s)')
        self.ax.set_ylabel('value')
        self.ax.grid(True)
        
        logger.info("visualizer initialized")

    def update(self, data: TestData):
        """update data"""
        self.data_x = data._data['time']
        self.data_y = data._data['value']
        
        # dynamically adjust x axis range
        if self.data_x:
            xmin, xmax = min(self.data_x), max(self.data_x)
            self.ax.set_xlim(xmin, xmax + 1)
        
        self.line.set_data(self.data_x, self.data_y)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        logger.debug(f"updating chart: data points={len(self.data_x)}")

async def generate_test_data():
    """generate test data"""
    test_data = TestData()
    visualizer = SimpleVisualizer()
    
    logger.info("starting to generate test data")
    for i in range(100):
        time = i * 0.1
        value = np.sin(time)
        test_data.add_point(time, value)
        visualizer.update(test_data)
        await asyncio.sleep(0.1)
        
        if i % 10 == 0:
            logger.info(f"generated {i} data points")

if __name__ == "__main__":
    plt.ion()  # enable interactive mode
    try:
        asyncio.run(generate_test_data())
    except KeyboardInterrupt:
        logger.info("test interrupted by user")
    finally:
        plt.ioff()  # disable interactive mode
        plt.show()  # keep chart displayed 
