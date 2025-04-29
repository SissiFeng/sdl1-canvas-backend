好的！
那我在刚才基础上，加上一个自动生成的标准目录（Table of Contents，TOC），排版更适合直接放到 GitHub 或其他文档系统里使用。
下面是最终带目录版的 .md 文件内容：

⸻

Biologic 实时数据可视化系统使用文档

📋 目录
	•	概述
	•	系统要求
	•	安装步骤
	•	使用方法
	•	连接 Biologic 设备并启动可视化服务器
	•	启动 Web 可视化服务器
	•	参数说明
	•	浏览器访问界面
	•	使用模拟数据进行测试
	•	支持的电化学技术
	•	用户界面说明
	•	故障排除
	•	高级配置
	•	多技术实验支持
	•	备注

⸻

概述

Biologic 实时数据可视化系统是一个基于 Web 的工具，用于实时显示 Biologic 电化学工作站产生的数据。
系统使用 WebSocket 技术将数据从 Biologic 设备实时推送到 Web 浏览器，并使用 Plotly.js 进行可视化，提供了良好的用户体验。

数据点会一个一个地显示出来，形成连续的图表，而不是重新绘制整个图表，便于实时观察电化学实验的进展。

⸻

系统要求
	•	Python 3.8 或更高版本
	•	Biologic 电化学工作站及其驱动程序
	•	现代 Web 浏览器（Chrome、Firefox、Edge 等）

⸻

安装步骤
	1.	克隆或下载代码库
	2.	创建并激活虚拟环境
	3.	安装依赖

pip install aiohttp plotly numpy matplotlib

	4.	安装 Biologic 驱动程序
确保已安装 Biologic 电化学工作站的驱动程序和 Python 接口。
如未安装，请参考 Biologic 官方文档。

⸻

使用方法

1. 连接 Biologic 设备并启动可视化服务器
	•	确保 Biologic 设备已连接并开启。
	•	查找 Biologic 设备的 USB 端口（如 USB0、USB1）以确认连接。

2. 启动 Web 可视化服务器

常用命令格式：

python src/web_visualization.py --biologic-port USB0 --channel 1 --technique cv --host 0.0.0.0 --port 8765

3. 参数说明

参数	说明	默认值
--biologic-port	Biologic 设备端口	USB0
--channel	通道号	1
--technique	电化学技术（ocv, cv, peis, cp, lp）	cv
--host	WebSocket 服务器地址	0.0.0.0
--port	WebSocket 服务器端口	8765

4. 在浏览器中访问可视化界面

打开浏览器，访问：

http://localhost:8765

即可实时查看 Biologic 产生的数据。

⸻

使用模拟数据进行测试（无需 Biologic 设备）

使用模拟数据命令示例：

python src/simulator.py --technique cv --delay 0.1 --interval 5 --host 0.0.0.0 --port 8765

参数	说明	默认值
--technique	要模拟的技术	cv
--delay	数据点之间的延迟（秒）	0.1
--interval	数据集之间的间隔（秒）	5



⸻

支持的电化学技术

技术	X 轴	Y 轴	特点
循环伏安法（CV）	电压 (V)	电流 (A)	显示氧化还原峰，曲线循环
开路电压（OCV）	时间 (s)	电压 (V)	电压随时间变化，较平稳
电化学阻抗谱（PEIS）	实部阻抗 (Ω)	负虚部阻抗 (Ω)	Nyquist图，通常呈半圆形
恒电流（CP）	时间 (s)	电压 (V)	电压随时间变化曲线
线性极化（LP）	电压 (V)	电流 (A)	近似线性的电压-电流曲线



⸻

用户界面说明
	•	标题栏：显示系统名称与连接状态（已连接/未连接）
	•	图表区域：实时更新绘制的图表
	•	信息面板：
	•	当前技术类型
	•	最新数据点（X, Y 值）
	•	统计信息（数据点总数、更新速率）

⸻

故障排除

无法连接到 Biologic 设备
	•	确认设备连接正确
	•	检查 USB 端口是否设置正确
	•	确认 Biologic 驱动和 Python 接口是否安装

浏览器无法显示数据
	•	检查浏览器控制台是否有错误
	•	确认 WebSocket 服务器是否已启动
	•	尝试刷新页面

数据显示异常
	•	检查选择的技术类型是否正确
	•	确认实验配置匹配

⸻

高级配置

1. 自定义电化学技术参数

修改 src/web_visualization.py 中的 create_techniques 函数，调整如扫描速率、电压范围等参数。

2. 自定义可视化设置

修改 src/web/js/realtime_chart.js 中的图表配置，如最大显示点数、样式等。

3. 集成到现有系统
	•	将 src/utils/websocket_server.py 和 src/web/ 目录集成到现有项目
	•	在数据采集代码中调用 WebSocket，推送数据点至前端实时可视化

⸻

多技术实验支持

系统支持在单次实验中连续切换多种技术（如 OCV → CV → PEIS）：
	•	检测到技术变化时自动发送 technique_change 事件
	•	前端动态更新图表标题、坐标轴、数据系列
	•	不需要刷新页面或重启服务器

⸻

备注
	•	所有电化学技术共用统一的可视化框架
	•	根据不同技术类型，自动调整数据解析与显示方式
	•	支持灵活扩展与参数自定义，适配各种电化学研究场景

如何切换不同的电化学技术
要切换到不同的电化学技术，只需在启动命令中更改--technique参数：

# 运行开路电压(OCV)实验
python src/web_visualization.py --biologic-port USB0 --technique ocv

# 运行电化学阻抗谱(PEIS)实验
python src/web_visualization.py --biologic-port USB0 --technique peis

# 运行恒电流(CP)实验
python src/web_visualization.py --biologic-port USB0 --technique cp

# 运行线性极化(LP)实验
python src/web_visualization.py --biologic-port USB0 --technique lp

多技术实验的可视化
系统也支持在同一实验中连续运行多种技术。例如，您可能想先运行OCV，然后是CV，最后是PEIS。在这种情况下，系统会自动检测技术的变化，并相应地更新图表的标题和坐标轴。

当技术变化时，系统会：

发送一个technique_change事件到前端
前端会更新图表标题和坐标轴标签
为新技术创建一个新的数据系列
开始绘制新技术的数据点
这样，您可以在同一界面中看到不同电化学技术的实时数据，而不需要切换页面或重启服务器。

自定义技术参数
如果您需要调整特定技术的参数（如扫描速率、电压范围等），可以修改src/web_visualization.py文件中的create_techniques函数。例如，要修改PEIS的频率范围：

elif technique_name == "peis":
    # 电化学阻抗谱技术
    peis_params = PEISParams(
        vs_initial=False,
        initial_voltage_step=0.0,
        final_frequency=0.01,  # 修改为0.01Hz
        initial_frequency=200000,  # 修改为200kHz
        sweep=SweepMode.Logarithmic,
        amplitude_voltage=0.02,  # 修改为20mV
        frequency_number=60  # 修改为60个频率点
    )
    return [PEISTechnique(peis_params)]
所有支持的电化学技术都使用相同的可视化框架，只是数据的解释和显示方式会根据技术类型自动调整。这使得系统非常灵活，能够适应各种电化学实验的需求。

高阶自动化版本：
多技术实验执行脚本 (src/run_multi_technique.py)：
从YAML配置文件读取实验序列和参数
支持连续运行多种电化学技术
提供实时Web可视化

创建实验配置文件：
复制并修改templates/simple_experiment.yaml或templates/experiment_template.yaml
运行多技术实验：
python src/run_multi_technique.py my_experiment.yaml
