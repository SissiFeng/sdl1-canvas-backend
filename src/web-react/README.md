# Biologic 实时数据可视化 - React 前端

这是 Biologic 实时数据可视化系统的 React 前端界面，提供了更丰富的交互功能和更现代的用户界面。

## 功能特点

- **四区域布局**：顶部导航栏、左侧 Threads 区、中部主图区和右侧配置面板，以及底部数据表
- **实时数据可视化**：数据点一个一个地显示出来，形成连续的图表
- **多技术支持**：支持 CV、OCV、PEIS、CP、LP 等多种电化学技术
- **实验 Threads**：可以查看和管理多个实验记录，支持拖拽排序
- **配置面板**：通过拖拽模块配置实验参数
- **数据表格**：展示实验数据点，支持排序、搜索和导出

## 安装和运行

### 安装依赖

```bash
cd src/web-react
npm install
```

### 开发模式运行

```bash
npm start
```

这将启动开发服务器，并在浏览器中打开 http://localhost:3000。

### 构建生产版本

```bash
npm run build
```

这将在 `build` 目录中生成生产版本的静态文件。

## 使用方法

### 连接到 WebSocket 服务器

1. 确保 WebSocket 服务器已启动（使用 `src/mock_data_generator.py` 或 `src/web_visualization.py`）
2. 点击界面右上角的"连接"按钮

### 查看实时数据

- 中部主图区会显示实时数据
- 可以切换不同的图表类型（散点图、线图、热图）
- 悬停在数据点上可以查看详细信息
- 点击数据点可以在数据表中高亮显示对应的行

### 管理实验 Threads

- 左侧面板显示所有实验 Threads
- 点击 Thread 可以切换到对应的实验数据
- 可以拖拽 Thread 来改变顺序

### 配置实验参数

- 右侧面板包含可拖拽的技术模块
- 可以配置各种实验参数
- 支持维度映射（X 轴和 Y 轴）

### 查看和导出数据

- 底部数据表显示所有数据点
- 可以搜索、排序和分页
- 点击"导出 CSV"按钮可以导出数据

## 与后端集成

前端通过 WebSocket 连接到后端服务器，接收实时数据。默认连接到 `ws://localhost:8765/ws`。

## 技术栈

- React
- Ant Design
- Plotly.js
- React Table
- React Beautiful DnD
