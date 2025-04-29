import React, { useState, useEffect, useMemo } from 'react';
import { Card, Radio, Typography, Space, Spin } from 'antd';
import Plot from 'react-plotly.js';

const { Title } = Typography;

// 辅助函数，确保任何值都被转换为有效的字符串
const ensureString = (value) => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'string') return value;
  if (typeof value === 'object' && value !== null) {
    if (value.hasOwnProperty('text')) return String(value.text);
    return JSON.stringify(value);
  }
  return String(value);
};

const MainChartArea = ({ chartData, currentTechnique, selectedPoint, onPointSelect }) => {
  const [chartType, setChartType] = useState('scatter');
  const [loading, setLoading] = useState(false);
  const [revisionCounter, setRevisionCounter] = useState(0);
  
  // 确保 currentTechnique 是字符串
  const safeTechnique = useMemo(() => ensureString(currentTechnique), [currentTechnique]);
  
  // 当接收到新数据时增加版本号，强制 Plotly 重新渲染
  useEffect(() => {
    if (chartData && Object.keys(chartData).length > 0) {
      console.log('Chart data updated, forcing re-render with revision:', revisionCounter + 1);
      setRevisionCounter(prev => prev + 1);
      
      // 输出当前的图表数据状态，用于调试
      Object.entries(chartData).forEach(([technique, data]) => {
        console.log(`Technique: ${technique}, Points: ${data.x.length}, Last point: (${data.x[data.x.length-1]}, ${data.y[data.y.length-1]})`);
      });
    }
  }, [chartData]);
  
  // 使用 useMemo 而不是 useState + useEffect 来计算 plotData
  const plotData = useMemo(() => {
    console.log('Recalculating plot data', chartData);
    
    if (!chartData || Object.keys(chartData).length === 0) {
      return [];
    }

    return Object.entries(chartData).map(([technique, data]) => {
      if (!data || !data.x || !data.y || data.x.length === 0 || data.y.length === 0) {
        console.warn('Invalid data for technique:', technique, data);
        return null;
      }
      
      // 确保技术名称是字符串
      const safeTechniqueName = ensureString(technique);
      
      const baseTrace = {
        x: data.x,
        y: data.y,
        name: safeTechniqueName,
      };

      if (chartType === 'scatter') {
        return {
          ...baseTrace,
          type: 'scatter',
          mode: 'lines+markers',
          marker: { size: 6 },
          line: { width: 2 }
        };
      } else if (chartType === 'line') {
        return {
          ...baseTrace,
          type: 'scatter',
          mode: 'lines',
          line: { width: 2 }
        };
      } else if (chartType === 'heatmap') {
        // For heatmap, we need to transform the data
        try {
          const uniqueX = Array.from(new Set(data.x)).sort((a, b) => a - b);
          const uniqueY = Array.from(new Set(data.y)).sort((a, b) => a - b);
          
          return {
            x: uniqueX,
            y: uniqueY,
            z: [data.y.slice(0, uniqueX.length)], // Simplified - real heatmap would need a 2D array
            type: 'heatmap',
            name: safeTechniqueName
          };
        } catch (error) {
          console.error('Error creating heatmap:', error);
          return null;
        }
      }
      
      return baseTrace;
    }).filter(Boolean); // 过滤掉 null 值
  }, [chartData, chartType]);
  
  // 使用 useMemo 为 layout 计算
  const layout = useMemo(() => {
    let xAxisTitle = 'X';
    let yAxisTitle = 'Y';
    let title = 'Biologic Real-time Data';

    // Set axis titles based on technique
    if (safeTechnique) {
      title = `${safeTechnique} Data`;
      
      if (safeTechnique === 'CV' || safeTechnique === 'LP') {
        xAxisTitle = 'Voltage (V)';
        yAxisTitle = 'Current (A)';
      } else if (safeTechnique === 'PEIS') {
        xAxisTitle = 'Re(Z) (Ω)';
        yAxisTitle = '-Im(Z) (Ω)';
      } else if (safeTechnique === 'OCV' || safeTechnique === 'CP') {
        xAxisTitle = 'Time (s)';
        yAxisTitle = 'Voltage (V)';
      }
    }

    return {
      autosize: true,
      title: title,
      showlegend: true,
      legend: {
        x: 0,
        y: 1,
        orientation: 'h'
      },
      xaxis: {
        title: xAxisTitle,
        showgrid: true,
        zeroline: true
      },
      yaxis: {
        title: yAxisTitle,
        showgrid: true,
        zeroline: true
      },
      margin: {
        l: 50,
        r: 50,
        b: 50,
        t: 50,
        pad: 4
      },
      // 添加过渡动画配置
      transition: {
        duration: 50, // 更快的过渡动画
        easing: 'linear'
      },
      // 确保图表自动调整范围以包含所有数据点
      uirevision: 'true' // 保持用户缩放等UI状态
    };
  }, [safeTechnique]);

  // 在加载数据时显示加载状态
  useEffect(() => {
    if (chartData && Object.keys(chartData).length > 0) {
      setLoading(false);
    }
  }, [chartData]);

  // Handle chart click - 确保点击数据也使用字符串作为技术名称
  const handleChartClick = (event) => {
    if (event.points && event.points.length > 0) {
      const point = event.points[0];
      onPointSelect({
        technique: ensureString(point.data.name),
        x: point.x,
        y: point.y,
        pointIndex: point.pointIndex
      });
    }
  };

  // 安全地提取标题文本
  const cardTitle = typeof layout.title === 'string' ? layout.title : 'Biologic Real-time Data';
  
  return (
    <Card style={{ width: '100%', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={4}>{cardTitle}</Title>
        <Radio.Group value={chartType} onChange={e => setChartType(e.target.value)}>
          <Radio.Button value="scatter">Scatter</Radio.Button>
          <Radio.Button value="line">Line</Radio.Button>
          <Radio.Button value="heatmap">Heatmap</Radio.Button>
        </Radio.Group>
      </div>
      
      <div className="chart-container" style={{ position: 'relative', minHeight: '400px' }}>
        <Spin spinning={loading} tip="Loading data...">
          {plotData.length > 0 ? (
            <Plot
              data={plotData}
              layout={layout}
              config={{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                scrollZoom: true // 添加滚动缩放功能
              }}
              onClick={handleChartClick}
              style={{ width: '100%', height: '400px' }}
              useResizeHandler={true}
              revision={revisionCounter} // 添加版本号以强制重新渲染
              onInitialized={(figure) => {
                console.log('Plot initialized with data:', figure.data);
              }}
              onUpdate={(figure) => {
                console.log('Plot updated with data:', figure.data);
              }}
            />
          ) : (
            <div style={{ 
              width: '100%', 
              height: '400px', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              background: '#f5f5f5',
              borderRadius: '4px'
            }}>
              <Space direction="vertical" align="center">
                <Title level={5} style={{ margin: 0 }}>No data available</Title>
                <Typography.Text type="secondary">
                  Connect to a Biologic device to see real-time data
                </Typography.Text>
              </Space>
            </div>
          )}
        </Spin>
      </div>
    </Card>
  );
};

export default MainChartArea;
