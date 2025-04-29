# Biologic Real-time Data Visualization

这个系统提供了Biologic电化学工作站数据的实时Web可视化功能。它使用WebSocket技术将数据从Biologic设备实时推送到Web浏览器，并使用Plotly.js进行可视化。

## 功能特点

- 实时数据可视化：数据点一个一个地显示出来
- 支持多种电化学技术：CV、OCV、PEIS、CP、LP等
- 响应式设计：适应不同屏幕尺寸
- 自动重连：在连接断开时自动重新连接
- 数据统计：显示数据点数量和更新速率

## 使用方法

### 使用真实设备

```bash
# 启动Web可视化服务器，连接到Biologic设备
python src/web_visualization.py --biologic-port USB0 --technique cv
```

### 使用模拟数据（用于测试）

```bash
# 启动模拟数据生成器
python src/mock_data_generator.py --technique cv --delay 0.1
```

## 命令行参数

### web_visualization.py

- `--biologic-port`: Biologic USB端口（默认：USB0）
- `--channel`: Biologic通道（默认：1）
- `--host`: WebSocket服务器主机（默认：0.0.0.0）
- `--port`: WebSocket服务器端口（默认：8765）
- `--technique`: 要运行的技术（默认：cv，可选：ocv, cv, peis, cp, lp）
- `--mock`: 使用模拟数据而不是真实设备

### mock_data_generator.py

- `--host`: WebSocket服务器主机（默认：0.0.0.0）
- `--port`: WebSocket服务器端口（默认：8765）
- `--technique`: 要模拟的技术（默认：cv，可选：ocv, cv, peis, cp, lp）
- `--delay`: 数据点之间的延迟（秒）（默认：0.1）
- `--interval`: 数据集之间的间隔（秒）（默认：5）

## 访问Web界面

启动服务器后，在浏览器中访问：

```
http://localhost:8765
```

## 技术栈

- 后端：Python、aiohttp、asyncio
- 前端：HTML、CSS、JavaScript、Plotly.js
- 通信：WebSocket
