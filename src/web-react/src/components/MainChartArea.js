import React, { useState, useEffect } from 'react';
import { Card, Radio, Typography, Space } from 'antd';
import Plot from 'react-plotly.js';

const { Title } = Typography;

const MainChartArea = ({ chartData, currentTechnique, selectedPoint, onPointSelect }) => {
  const [chartType, setChartType] = useState('scatter');
  const [plotData, setPlotData] = useState([]);
  const [layout, setLayout] = useState({
    autosize: true,
    title: 'Biologic Real-time Data',
    showlegend: true,
    legend: {
      x: 0,
      y: 1,
      orientation: 'h'
    },
    xaxis: {
      title: 'X',
      showgrid: true,
      zeroline: true
    },
    yaxis: {
      title: 'Y',
      showgrid: true,
      zeroline: true
    },
    margin: {
      l: 50,
      r: 50,
      b: 50,
      t: 50,
      pad: 4
    }
  });

  // Update plot data when chartData changes
  useEffect(() => {
    if (Object.keys(chartData).length === 0) {
      setPlotData([]);
      return;
    }

    const newPlotData = Object.entries(chartData).map(([technique, data]) => {
      const baseTrace = {
        x: data.x,
        y: data.y,
        name: technique,
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
        // This is a simplified example - real heatmap would need more processing
        return {
          x: Array.from(new Set(data.x)).sort((a, b) => a - b),
          y: Array.from(new Set(data.y)).sort((a, b) => a - b),
          z: [data.y], // Simplified - real heatmap would need a 2D array
          type: 'heatmap',
          name: technique
        };
      }
      
      return baseTrace;
    });

    setPlotData(newPlotData);
  }, [chartData, chartType]);

  // Update layout when currentTechnique changes
  useEffect(() => {
    if (!currentTechnique) return;

    let xAxisTitle = 'X';
    let yAxisTitle = 'Y';

    // Set axis titles based on technique
    if (currentTechnique === 'CV' || currentTechnique === 'LP') {
      xAxisTitle = 'Voltage (V)';
      yAxisTitle = 'Current (A)';
    } else if (currentTechnique === 'PEIS') {
      xAxisTitle = 'Re(Z) (Ω)';
      yAxisTitle = '-Im(Z) (Ω)';
    } else if (currentTechnique === 'OCV' || currentTechnique === 'CP') {
      xAxisTitle = 'Time (s)';
      yAxisTitle = 'Voltage (V)';
    }

    setLayout(prevLayout => ({
      ...prevLayout,
      title: `${currentTechnique} Data`,
      xaxis: {
        ...prevLayout.xaxis,
        title: xAxisTitle
      },
      yaxis: {
        ...prevLayout.yaxis,
        title: yAxisTitle
      }
    }));
  }, [currentTechnique]);

  // Handle chart click
  const handleChartClick = (event) => {
    if (event.points && event.points.length > 0) {
      const point = event.points[0];
      onPointSelect({
        technique: point.data.name,
        x: point.x,
        y: point.y,
        pointIndex: point.pointIndex
      });
    }
  };

  return (
    <Card style={{ width: '100%', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={4}>{layout.title}</Title>
        <Radio.Group value={chartType} onChange={e => setChartType(e.target.value)}>
          <Radio.Button value="scatter">Scatter</Radio.Button>
          <Radio.Button value="line">Line</Radio.Button>
          <Radio.Button value="heatmap">Heatmap</Radio.Button>
        </Radio.Group>
      </div>
      
      <div className="chart-container">
        {plotData.length > 0 ? (
          <Plot
            data={plotData}
            layout={layout}
            config={{
              responsive: true,
              displayModeBar: true,
              displaylogo: false,
              modeBarButtonsToRemove: ['lasso2d', 'select2d']
            }}
            onClick={handleChartClick}
            style={{ width: '100%', height: '100%' }}
          />
        ) : (
          <div style={{ 
            width: '100%', 
            height: '100%', 
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
      </div>
    </Card>
  );
};

export default MainChartArea;
