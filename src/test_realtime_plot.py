"""
实时数据显示测试模块
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

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@dataclass
class TestData:
    """测试数据类"""
    time: Optional[float] = None
    value: Optional[float] = None
    technique_type: str = 'TestTechnique'
    _data: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))

    def add_point(self, time: float, value: float):
        """添加数据点"""
        self.time = time
        self.value = value
        self._data['time'].append(time)
        self._data['value'].append(value)
        logger.debug(f"添加数据点: time={time}, value={value}")

    def to_json(self) -> Dict[str, List[float]]:
        """转换为JSON格式"""
        return {k: list(v) for k, v in self._data.items()}

class SimpleVisualizer:
    """简单的实时可视化器"""
    def __init__(self):
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], 'b-')
        self.data_x = []
        self.data_y = []
        
        # 设置图表
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(-1.5, 1.5)
        self.ax.set_title('实时数据显示测试')
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('数值')
        self.ax.grid(True)
        
        logger.info("可视化器初始化完成")

    def update(self, data: TestData):
        """更新数据"""
        self.data_x = data._data['time']
        self.data_y = data._data['value']
        
        # 动态调整 x 轴范围
        if self.data_x:
            xmin, xmax = min(self.data_x), max(self.data_x)
            self.ax.set_xlim(xmin, xmax + 1)
        
        self.line.set_data(self.data_x, self.data_y)
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        
        logger.debug(f"更新图表: 数据点数={len(self.data_x)}")

async def generate_test_data():
    """生成测试数据"""
    test_data = TestData()
    visualizer = SimpleVisualizer()
    
    logger.info("开始生成测试数据")
    for i in range(100):
        time = i * 0.1
        value = np.sin(time)
        test_data.add_point(time, value)
        visualizer.update(test_data)
        await asyncio.sleep(0.1)
        
        if i % 10 == 0:
            logger.info(f"已生成 {i} 个数据点")

if __name__ == "__main__":
    plt.ion()  # 启用交互模式
    try:
        asyncio.run(generate_test_data())
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    finally:
        plt.ioff()  # 关闭交互模式
        plt.show()  # 保持图表显示 
