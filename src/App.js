import React, { useState, useEffect } from 'react';
import { Layout, theme } from 'antd';
import TopNavBar from './components/TopNavBar';
import ThreadsPanel from './components/ThreadsPanel';
import MainChartArea from './components/MainChartArea';
import ConfigPanel from './components/ConfigPanel';
import DataTable from './components/DataTable';
import useWebSocket from './hooks/useWebSocket';
import './App.css';

const { Header, Sider, Content, Footer } = Layout;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [threads, setThreads] = useState([]);
  const [currentThread, setCurrentThread] = useState(null);
  const [chartData, setChartData] = useState({});
  const [dataPoints, setDataPoints] = useState([]);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [configVisible, setConfigVisible] = useState(true);
  
  const {
    status,
    data,
    currentTechnique,
    connect,
    disconnect
  } = useWebSocket('ws://localhost:8765/ws');

  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // Effect to handle incoming data
  useEffect(() => {
    if (data && data.type === 'data_point') {
      // Add data point to chart data
      setChartData(prevData => {
        const technique = data.technique;
        const newData = { ...prevData };
        
        if (!newData[technique]) {
          newData[technique] = {
            x: [],
            y: [],
            type: 'scatter',
            mode: 'lines+markers',
            name: technique
          };
        }
        
        newData[technique].x.push(data.x);
        newData[technique].y.push(data.y);
        
        return newData;
      });
      
      // Add data point to data table
      setDataPoints(prevPoints => [
        ...prevPoints,
        {
          id: prevPoints.length,
          technique: data.technique,
          x: data.x,
          y: data.y,
          timestamp: new Date().toISOString()
        }
      ]);
      
      // Update threads if needed
      if (threads.length === 0 || threads[threads.length - 1].technique !== data.technique) {
        const newThread = {
          id: threads.length + 1,
          title: `${data.technique}-${threads.length + 1}`,
          technique: data.technique,
          timestamp: new Date().toISOString(),
          data: {
            x: [data.x],
            y: [data.y]
          }
        };
        
        setThreads(prevThreads => [...prevThreads, newThread]);
        
        if (!currentThread) {
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
    }
  }, [data, threads, currentThread]);

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
    setSelectedPoint(pointData);
  };

  // Handle export data
  const handleExportData = () => {
    if (dataPoints.length === 0) return;
    
    const csv = [
      'id,technique,x,y,timestamp',
      ...dataPoints.map(point => 
        `${point.id},${point.technique},${point.x},${point.y},${point.timestamp}`
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
          onConnect={connect}
          onDisconnect={disconnect}
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
