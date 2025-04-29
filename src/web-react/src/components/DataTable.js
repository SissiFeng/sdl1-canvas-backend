import React, { useState, useMemo, useCallback } from 'react';
import { Table, Typography, Button, Input, Space } from 'antd';
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons';

const { Title } = Typography;

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

const DataTable = ({ dataPoints, selectedPoint, onPointSelect }) => {
  const [searchText, setSearchText] = useState('');
  const [pageSize, setPageSize] = useState(10);
  
  // 使用 useMemo 缓存过滤后的数据，避免每次渲染都重新计算
  const filteredData = useMemo(() => {
    if (!dataPoints || dataPoints.length === 0) return [];
    if (!searchText) return dataPoints;
    
    const searchTextLower = searchText.toLowerCase();
    return dataPoints.filter(item => {
      return (
        (item.id !== undefined && String(item.id).includes(searchTextLower)) ||
        (item.technique && ensureString(item.technique).toLowerCase().includes(searchTextLower)) ||
        (item.x !== undefined && String(item.x).includes(searchTextLower)) ||
        (item.y !== undefined && String(item.y).includes(searchTextLower)) ||
        (item.timestamp && String(item.timestamp).toLowerCase().includes(searchTextLower))
      );
    });
  }, [dataPoints, searchText]);
  
  // 使用 useMemo 缓存表格列配置
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Technique',
      dataIndex: 'technique',
      key: 'technique',
      render: (text) => ensureString(text),
      sorter: (a, b) => {
        const textA = ensureString(a.technique);
        const textB = ensureString(b.technique);
        return textA.localeCompare(textB);
      },
    },
    {
      title: 'X',
      dataIndex: 'x',
      key: 'x',
      render: (value) => typeof value === 'number' ? value.toFixed(6) : (value || 'N/A'),
      sorter: (a, b) => {
        const numA = typeof a.x === 'number' ? a.x : 0;
        const numB = typeof b.x === 'number' ? b.x : 0;
        return numA - numB;
      },
    },
    {
      title: 'Y',
      dataIndex: 'y',
      key: 'y',
      render: (value) => typeof value === 'number' ? value.toFixed(6) : (value || 'N/A'),
      sorter: (a, b) => {
        const numA = typeof a.y === 'number' ? a.y : 0;
        const numB = typeof b.y === 'number' ? b.y : 0;
        return numA - numB;
      },
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (value) => value ? new Date(value).toLocaleString() : 'N/A',
      sorter: (a, b) => {
        if (!a.timestamp || !b.timestamp) return 0;
        return new Date(a.timestamp) - new Date(b.timestamp);
      },
    },
  ], []);
  
  // 导出CSV
  const handleExportCSV = () => {
    if (dataPoints.length === 0) return;
    
    const csv = [
      'id,technique,x,y,timestamp',
      ...dataPoints.map(point => 
        `${point.id},${ensureString(point.technique)},${point.x || ''},${point.y || ''},${point.timestamp || ''}`
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

  // 使用 useMemo 缓存表格行配置
  const getRowProps = useCallback((record) => ({
    onClick: () => {
      onPointSelect({
        technique: ensureString(record.technique),
        x: record.x,
        y: record.y
      });
    },
  }), [onPointSelect]);

  // 使用 useMemo 缓存分页配置
  const paginationConfig = useMemo(() => ({
    pageSize: pageSize,
    total: filteredData.length,
    showSizeChanger: true,
    showQuickJumper: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    onChange: (page, size) => {
      if (size !== pageSize) {
        setPageSize(size);
      }
    },
  }), [filteredData.length, pageSize]);

  return (
    <div className="data-table-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={4}>Data Points</Title>
        <Space>
          <Input
            placeholder="Search data..."
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
          />
          <Button 
            icon={<DownloadOutlined />} 
            onClick={handleExportCSV}
            disabled={dataPoints.length === 0}
          >
            Export CSV
          </Button>
        </Space>
      </div>
      
      <Table
        rowKey="id"
        dataSource={filteredData}
        columns={columns}
        rowClassName={(record) => {
          if (selectedPoint && 
              selectedPoint.technique === record.technique && 
              selectedPoint.x === record.x && 
              selectedPoint.y === record.y) {
            return 'selected-row';
          }
          return '';
        }}
        onRow={getRowProps}
        pagination={paginationConfig}
        size="small"
        scroll={{ x: 'max-content' }}
      />
    </div>
  );
};

export default DataTable;
