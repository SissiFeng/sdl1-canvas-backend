# Biologic 实时数据可视化系统

这个系统提供了Biologic电化学工作站数据的实时Web可视化功能，支持多种电化学技术的连续运行和实时监控。

## 主要功能

- **实时数据可视化**：数据点一个一个地显示出来，形成连续的图表
- **多技术支持**：支持CV、OCV、PEIS、CP、LP等多种电化学技术
- **简单配置**：通过YAML配置文件轻松定义实验序列和参数
- **WebSocket通信**：使用WebSocket技术实现高效的实时数据传输
- **响应式设计**：适应不同屏幕尺寸的Web界面

## 快速开始

### 安装

```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate

# 安装依赖
pip install aiohttp plotly numpy matplotlib pyyaml
```

### 运行单一技术实验

```bash
# 使用真实Biologic设备
python src/web_visualization.py --biologic-port USB0 --technique cv

# 使用模拟数据进行测试
python src/mock_data_generator.py --technique cv --delay 0.2
```

### 运行多技术实验

```bash
# 使用真实Biologic设备
python src/run_multi_technique.py templates/simple_experiment.yaml

# 使用模拟数据进行测试
python src/run_multi_technique.py templates/simple_experiment.yaml --mock
```

### 查看可视化

在浏览器中访问：
```
http://localhost:8765
```

## 文档

详细文档请参阅：

- [多技术实验指南](docs/multi_technique_guide.md)
- [配置模板](templates/)

## 支持的电化学技术

| 技术 | 代码 | 描述 | X轴 | Y轴 |
|------|------|------|-----|-----|
| 循环伏安法 | cv | 在电位窗口内循环扫描电压 | 电压(V) | 电流(A) |
| 开路电压 | ocv | 测量开路电压随时间变化 | 时间(s) | 电压(V) |
| 电化学阻抗谱 | peis | 测量不同频率下的阻抗 | 实部阻抗(Ω) | -虚部阻抗(Ω) |
| 恒电流 | cp | 施加恒定电流并测量电压响应 | 时间(s) | 电压(V) |
| 线性极化 | lp | 线性扫描电压并测量电流响应 | 电压(V) | 电流(A) |

## 自定义实验

1. 复制一个配置模板：
   ```bash
   cp templates/simple_experiment.yaml my_experiment.yaml
   ```

2. 编辑配置文件，定义您的实验序列和参数

3. 运行实验：
   ```bash
   python src/run_multi_technique.py my_experiment.yaml
   ```

## 配置文件示例

### 简化配置示例

```yaml
# 设备连接配置
device:
  port: "USB0"  # Biologic设备端口
  channel: 1    # 使用的通道号

# 实验序列
sequence:
  # 开路电压测量
  - technique: "ocv"
    duration: 60  # 秒
  
  # 循环伏安法
  - technique: "cv"
    voltage_range: [-0.5, 0.5]  # 电压范围 [起始V, 结束V]
    scan_rate: 0.05  # V/s
    cycles: 3
  
  # 电化学阻抗谱
  - technique: "peis"
    frequency_range: [100000, 0.1]  # [起始Hz, 结束Hz]
    amplitude: 0.01  # V
```

### 完整配置示例

```yaml
# 设备连接配置
device:
  port: "USB0"
  channel: 1

# 可视化服务器配置
visualization:
  host: "0.0.0.0"
  port: 8765

# 实验序列
sequence:
  - technique: "ocv"
    params:
      rest_time: 60
      record_every_dt: 0.1
  
  - technique: "cv"
    params:
      voltage_step: 0.5
      scan_rate: 0.05
      n_cycles: 3
      record_every_dE: 0.001
```

## 系统要求

- Python 3.8 或更高版本
- Biologic 电化学工作站及其驱动程序
- 现代 Web 浏览器（Chrome、Firefox、Edge 等）

## 故障排除

### 无法连接到Biologic设备
- 确保设备已正确连接并开启
- 检查配置文件中的端口设置
- 尝试使用`blfind`工具查找可用设备：
  ```python
  python -c "from biologic.extras.blfind import main; main()"
  ```

### 可视化问题
- 确保浏览器支持WebSocket
- 检查浏览器控制台是否有错误信息
- 尝试刷新页面
