### 实验人员使用指南

#### 1. 环境准备
```bash
# 1.1 克隆仓库

# 1.2 创建并激活虚拟环境

# 1.3 安装依赖
pip install -r requirements.txt
```

#### 2. 硬件连接
1. 连接 Opentrons OT-2 机器人（确保网络连接）
2. 连接 Arduino 控制的泵系统（通过 USB）
3. 连接 Biologic 电化学工作站（通过 USB）
4. 记录各设备的连接端口信息

#### 3. 运行实验
根据实验需求，选择以下命令之一：

```bash
# 3.1 运行完整实验（沉积+表征）
python src/main.py --run-number 001 --well C5 --experiment-type full

# 3.2 仅运行沉积实验
python src/main.py --run-number 002 --well C5 --experiment-type deposition --deposition-current -0.003

# 3.3 仅运行表征实验
python src/main.py --run-number 003 --well C5 --experiment-type characterization
```

常用参数说明：
- `--run-number`：实验编号（必填）
- `--well`：实验孔位置（必填，如 'C5'）
- `--experiment-type`：实验类型（必填，选择 'deposition'、'characterization' 或 'full'）
- `--robot-ip`：OT-2机器人IP地址（默认：100.67.89.154）
- `--arduino-port`：Arduino设备端口
- `--biologic-port`：Biologic设备USB端口（默认：USB0）
- `--deposition-current`：沉积电流（安培，默认：-0.002）
- `--deposition-duration`：沉积时间（秒，默认：60）

#### 4. 数据获取
实验数据将自动保存在 `data/` 目录下：
```
data/
└── YYYYMMDD_RUN/
    ├── deposition/
    │   └── YYYYMMDD_RUN_XX_TECHNIQUE.csv
    └── characterization/
        └── YYYYMMDD_RUN_XX_TECHNIQUE.csv
```

#### 5. 日志查看
- 实验日志保存在 `logs/` 目录
- 文件名格式：`YYYYMMDD_RUN.log`
- 包含设备连接状态、实验进度、错误信息等

