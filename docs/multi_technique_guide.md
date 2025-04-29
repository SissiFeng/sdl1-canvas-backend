# Biologic 多技术实验可视化系统使用指南

本指南将帮助您使用多技术实验可视化系统，通过简单的配置文件连续运行多种电化学技术，并实时可视化结果。

## 1. 系统概述

多技术实验可视化系统允许您：

- 通过简单的YAML配置文件定义实验序列
- 连续运行多种电化学技术（CV、OCV、PEIS、CP、LP等）
- 实时可视化实验数据
- 自动保存实验结果

## 2. 安装和准备

### 2.1 安装依赖

```bash
# 创建并激活虚拟环境
python -m venv venv
source venv/bin/activate  # 在Windows上使用: venv\Scripts\activate

# 安装依赖
pip install aiohttp plotly numpy matplotlib pyyaml
```

### 2.2 确保Biologic设备已连接

确保您的Biologic设备已正确连接到计算机并已开启。您可以使用以下命令查找已连接的设备：

```bash
source venv/bin/activate
python -c "from biologic.extras.blfind import main; main()"
```

## 3. 创建实验配置文件

系统提供了两种配置模板：

### 3.1 简化配置模板

适合初学者使用，参数更简洁直观：

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
```

### 3.2 完整配置模板

提供更多高级参数控制：

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

您可以在`templates`目录中找到这两种模板，复制并根据需要修改。

## 4. 运行多技术实验

### 4.1 使用真实Biologic设备

```bash
source venv/bin/activate
python src/run_multi_technique.py templates/simple_experiment.yaml
```

### 4.2 使用模拟数据进行测试

```bash
source venv/bin/activate
python src/run_multi_technique.py templates/simple_experiment.yaml --mock
```

## 5. 查看实时可视化

启动实验后，在浏览器中访问：

```
http://localhost:8765
```

您将看到实时数据可视化界面，数据点会随着实验的进行而一个一个地显示出来。当实验切换到新的技术时，图表会自动更新标题和坐标轴。

## 6. 支持的电化学技术

系统支持以下电化学技术：

| 技术 | 代码 | 描述 | X轴 | Y轴 |
|------|------|------|-----|-----|
| 循环伏安法 | cv | 在电位窗口内循环扫描电压 | 电压(V) | 电流(A) |
| 开路电压 | ocv | 测量开路电压随时间变化 | 时间(s) | 电压(V) |
| 电化学阻抗谱 | peis | 测量不同频率下的阻抗 | 实部阻抗(Ω) | -虚部阻抗(Ω) |
| 恒电流 | cp | 施加恒定电流并测量电压响应 | 时间(s) | 电压(V) |
| 线性极化 | lp | 线性扫描电压并测量电流响应 | 电压(V) | 电流(A) |

## 7. 自定义配置参数

### 7.1 通用参数

所有技术都支持以下参数：

- `technique`: 技术类型（"cv", "ocv", "peis", "cp", "lp"）

### 7.2 技术特定参数

#### 开路电压(OCV)
- `duration` 或 `rest_time`: 测量时间(秒)
- `record_interval` 或 `record_every_dt`: 数据记录间隔(秒)

#### 循环伏安法(CV)
- `voltage_range`: 电压范围 [起始V, 结束V]
- `scan_rate`: 扫描速率(V/s)
- `cycles` 或 `n_cycles`: 循环次数
- `record_interval` 或 `record_every_dE`: 数据记录间隔(V)

#### 电化学阻抗谱(PEIS)
- `frequency_range`: 频率范围 [起始Hz, 结束Hz]
- `amplitude` 或 `amplitude_voltage`: 振幅电压(V)
- `points` 或 `frequency_number`: 频率点数量
- `sweep`: 扫描模式("logarithmic"或"linear")

#### 恒电流(CP)
- `current`: 电流(A)
- `duration`: 持续时间(秒)
- `record_interval` 或 `record_every_dt`: 数据记录间隔(秒)

#### 线性极化(LP)
- `voltage_step`: 电压步长(V)
- `scan_rate`: 扫描速率(V/s)
- `record_interval` 或 `record_every_dE`: 数据记录间隔(V)

## 8. 数据保存

实验数据会自动保存在配置文件中指定的目录（默认为`data/experiments/[实验ID]`）。每个技术的数据都会保存为单独的CSV文件。

## 9. 故障排除

### 9.1 无法连接到Biologic设备
- 确保设备已正确连接并开启
- 检查配置文件中的端口设置
- 尝试使用`blfind`工具查找可用设备

### 9.2 可视化问题
- 确保浏览器支持WebSocket
- 检查浏览器控制台是否有错误信息
- 尝试刷新页面

## 10. 示例配置

### 10.1 电池充放电测试

```yaml
device:
  port: "USB0"
  channel: 1

sequence:
  # 开路电压稳定
  - technique: "ocv"
    duration: 300  # 5分钟稳定

  # 恒电流充电
  - technique: "cp"
    current: 0.001  # 1mA
    duration: 3600  # 1小时

  # 开路电压休息
  - technique: "ocv"
    duration: 600  # 10分钟休息

  # 恒电流放电
  - technique: "cp"
    current: -0.001  # -1mA
    duration: 3600  # 1小时
```

### 10.2 腐蚀研究

```yaml
device:
  port: "USB0"
  channel: 1

sequence:
  # 开路电压稳定
  - technique: "ocv"
    duration: 1800  # 30分钟稳定

  # 电化学阻抗谱
  - technique: "peis"
    frequency_range: [100000, 0.01]
    amplitude: 0.01

  # 线性极化
  - technique: "lp"
    voltage_step: 0.05
    scan_rate: 0.001
```

## 11. 进阶使用

### 11.1 自定义可视化设置

您可以通过修改配置文件中的`visualization`部分来自定义可视化设置：

```yaml
visualization:
  host: "0.0.0.0"  # 服务器主机地址
  port: 8765       # 服务器端口
  max_points: 1000 # 最大显示点数
```

### 11.2 集成到现有系统

如果您想将此系统集成到现有的实验控制系统中，可以导入`run_multi_technique.py`中的函数，并在您的代码中调用它们。
