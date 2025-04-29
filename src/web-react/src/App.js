import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Layout, theme, message } from 'antd';
import TopNavBar from './components/TopNavBar';
import ThreadsPanel from './components/ThreadsPanel';
import MainChartArea from './components/MainChartArea';
import ConfigPanel from './components/ConfigPanel';
import DataTable from './components/DataTable';
import useWebSocket from './hooks/useWebSocket';
import './App.css';

const { Header, Sider, Content, Footer } = Layout;

// 辅助函数，确保值是字符串类型
const ensureString = (value) => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'object' && value !== null) {
    if (value.hasOwnProperty('text')) return String(value.text);
    return JSON.stringify(value);
  }
  return String(value);
};

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [chartData, setChartData] = useState({});
  const [dataPoints, setDataPoints] = useState([]);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [configVisible, setConfigVisible] = useState(true);
  
  // 使用 useRef 跟踪最新的状态，避免 useEffect 依赖过多导致的循环
  const threadsRef = useRef(threads);
  const currentThreadRef = useRef(currentThread);
  const dataPointsRef = useRef(dataPoints);
  
  // 在 threads 或 currentThread 变化时更新 ref
  useEffect(() => {
    threadsRef.current = threads;
    currentThreadRef.current = currentThread;
  }, [threads, currentThread]);
  
  // 在 dataPoints 变化时更新 ref
  useEffect(() => {
    dataPointsRef.current = dataPoints;
  }, [dataPoints]);
  
  // 使用 useCallback 确保函数引用稳定
  const handleConnect = useCallback(() => {
    console.log('Manual connect requested');
    if (connect) {
      connect();
    }
  }, []);
  
  const handleDisconnect = useCallback(() => {
    console.log('Manual disconnect requested');
    if (disconnect) {
      disconnect();
    }
  }, []);
  
  const {
    status,
    data,
    currentTechnique,
    connect,
    disconnect
  } = useWebSocket('ws://localhost:3003/ws');

  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // Effect to handle incoming data
  useEffect(() => {
    if (!data) return;
    
    console.log('Received data:', data);
    
    if (data.type === 'data_point') {
      try {
        // 确保技术名称是字符串
        const techniqueName = ensureString(data.technique);
        
        // Add data point to chart data - 创建完全新的对象以确保状态变化被检测到
        setChartData(prevData => {
          // 浅拷贝顶层对象
          const newData = { ...prevData };
          
          // 获取或初始化技术数据对象
          const techniqueData = newData[techniqueName] 
            ? { ...newData[techniqueName] } 
            : {
                x: [],
                y: [],
                type: 'scatter',
                mode: 'lines+markers',
                name: techniqueName
              };
          
          // 创建新的数据数组
          techniqueData.x = [...(techniqueData.x || []), data.x];
          techniqueData.y = [...(techniqueData.y || []), data.y];
          
          // 更新技术数据对象
          newData[techniqueName] = techniqueData;
          
          console.log(`Updated chartData for ${techniqueName}, now has ${techniqueData.x.length} points`);
          console.log(`Last point: (${data.x}, ${data.y})`);
          
          return newData;
        });
        
        // Add data point to data table
        const newPoint = {
          id: dataPointsRef.current.length,
          technique: techniqueName,
          x: data.x,
          y: data.y,
          timestamp: new Date().toISOString()
        };
        
        setDataPoints(prevPoints => [...prevPoints, newPoint]);
        
        // Update threads if needed
        const currentThreads = threadsRef.current;
        const currentActiveThread = currentThreadRef.current;
        
        if (currentThreads.length === 0 || currentThreads[currentThreads.length - 1].technique !== techniqueName) {
          const newThread = {
            id: currentThreads.length + 1,
            title: `${techniqueName}-${currentThreads.length + 1}`,
            technique: techniqueName,
            timestamp: new Date().toISOString(),
            data: {
              x: [data.x],
              y: [data.y]
            }
          };
          
          setThreads(prevThreads => [...prevThreads, newThread]);
          
          if (!currentActiveThread) {
            setCurrentThread(newThread);
          }
        } else {
          // Update the last thread with new data
          setThreads(prevThreads => {
            const updatedThreads = [...prevThreads];
            const lastThread = { ...updatedThreads[updatedThreads.length - 1] };
            
            lastThread.data.x.push(data.x);
            lastThread.data.y.push(data.y);
            
            updatedThreads[updatedThreads.length - 1] = lastThread;
            return updatedThreads;
          });
        }
      } catch (error) {
        console.error('Error processing data:', error);
        message.error('Error processing data');
      }
    }
  }, [data]); // 简化依赖项，只依赖于 data

  // 自动重连监控
  useEffect(() => {
    if (status === 'connected') {
      console.log('WebSocket connected');
      message.success('Connected to data server');
    } else if (status === 'disconnected') {
      console.log('WebSocket disconnected');
      message.warning('Disconnected from data server');
    } else if (status === 'connecting') {
      console.log('WebSocket connecting...');
      message.loading('Connecting to data server...');
    }
  }, [status]);

  // 组件卸载时确保断开连接
  useEffect(() => {
    return () => {
      if (disconnect) {
        disconnect();
      }
    };
  }, [disconnect]);

  // Handle thread selection
  const handleThreadSelect = (thread) => {
    setCurrentThread(thread);
  };

  // Handle thread reordering
  const handleThreadReorder = (result) => {
    if (!result.destination) return;
    
    const items = Array.from(threads);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    setThreads(items);
  };

  // Handle point selection in chart
  const handlePointSelect = (pointData) => {
    // 确保所有字符串值都是安全的
    if (pointData && typeof pointData === 'object') {
      if (pointData.technique) {
        pointData.technique = ensureString(pointData.technique);
      }
    }
    setSelectedPoint(pointData);
  };

  // Handle export data
  const handleExportData = () => {
    if (dataPoints.length === 0) return;
    
    const csv = [
      'id,technique,x,y,timestamp',
      ...dataPoints.map(point => 
        `${point.id},${ensureString(point.technique)},${point.x},${point.y},${point.timestamp}`
      )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `biologic-data-${new Date().toISOString()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Handle reset
  const handleReset = () => {
    setChartData({});
    setDataPoints([]);
    setThreads([]);
    setCurrentThread(null);
    setSelectedPoint(null);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="header">
        <TopNavBar 
          connectionStatus={status} 
          onConnect={handleConnect}
          onDisconnect={handleDisconnect}
          onExport={handleExportData}
          onReset={handleReset}
        />
      </Header>
      <Layout>
        <Sider 
          width={300} 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          style={{ background: colorBgContainer }}
        >
          <ThreadsPanel 
            threads={threads}
            currentThread={currentThread}
            onThreadSelect={handleThreadSelect}
            onThreadReorder={handleThreadReorder}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          <Content
            style={{
              padding: 24,
              margin: 0,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <MainChartArea 
              chartData={chartData}
              currentTechnique={currentTechnique}
              selectedPoint={selectedPoint}
              onPointSelect={handlePointSelect}
            />
          </Content>
          <Footer style={{ padding: '24px 0' }}>
            <DataTable 
              dataPoints={dataPoints}
              selectedPoint={selectedPoint}
              onPointSelect={handlePointSelect}
            />
          </Footer>
        </Layout>
        <Sider 
          width={300} 
          collapsible 
          collapsed={rightCollapsed} 
          onCollapse={setRightCollapsed}
          collapsedWidth={0}
          reverseArrow
          style={{ background: colorBgContainer }}
          trigger={null}
        >
          <ConfigPanel 
            visible={configVisible}
            onClose={() => setConfigVisible(false)}
            currentTechnique={currentTechnique}
          />
        </Sider>
      </Layout>
    </Layout>
  );
}

export default App;
