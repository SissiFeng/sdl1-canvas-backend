import React, { useMemo } from 'react';
import { Table, Typography, Button, Input, Space } from 'antd';
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons';
import { useTable, useGlobalFilter, useSortBy, usePagination } from 'react-table';

const { Title } = Typography;

const DataTable = ({ dataPoints, selectedPoint, onPointSelect }) => {
  const columns = useMemo(
    () => [
      {
        Header: 'ID',
        accessor: 'id',
      },
      {
        Header: 'Technique',
        accessor: 'technique',
      },
      {
        Header: 'X',
        accessor: 'x',
        Cell: ({ value }) => value.toFixed(6),
      },
      {
        Header: 'Y',
        accessor: 'y',
        Cell: ({ value }) => value.toFixed(6),
      },
      {
        Header: 'Timestamp',
        accessor: 'timestamp',
        Cell: ({ value }) => new Date(value).toLocaleString(),
      },
    ],
    []
  );

  const data = useMemo(() => dataPoints, [dataPoints]);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    page,
    prepareRow,
    state,
    setGlobalFilter,
    gotoPage,
    pageCount,
    setPageSize,
    state: { pageIndex, pageSize, globalFilter },
  } = useTable(
    {
      columns,
      data,
      initialState: { pageSize: 10 },
    },
    useGlobalFilter,
    useSortBy,
    usePagination
  );

  const handleExportCSV = () => {
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

  return (
    <div className="data-table-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
        <Title level={4}>Data Points</Title>
        <Space>
          <Input
            placeholder="Search data..."
            value={globalFilter || ''}
            onChange={e => setGlobalFilter(e.target.value)}
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
        {...getTableProps()}
        rowClassName={(record) => {
          if (selectedPoint && 
              selectedPoint.technique === record.technique && 
              selectedPoint.x === record.x && 
              selectedPoint.y === record.y) {
            return 'selected-row';
          }
          return '';
        }}
        onRow={(record) => ({
          onClick: () => {
            onPointSelect({
              technique: record.technique,
              x: record.x,
              y: record.y
            });
          },
        })}
        columns={headerGroups[0].headers.map(column => ({
          ...column,
          title: column.render('Header'),
          dataIndex: column.id,
          key: column.id,
          sorter: true,
          sortOrder: column.isSorted
            ? column.isSortedDesc
              ? 'descend'
              : 'ascend'
            : undefined,
        }))}
        dataSource={page.map(row => {
          prepareRow(row);
          return { ...row.original, key: row.id };
        })}
        pagination={{
          current: pageIndex + 1,
          pageSize,
          total: dataPoints.length,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          onChange: (page, pageSize) => {
            gotoPage(page - 1);
            setPageSize(pageSize);
          },
          onShowSizeChange: (current, size) => {
            setPageSize(size);
          },
        }}
        size="small"
        scroll={{ x: 'max-content' }}
      />
    </div>
  );
};

export default DataTable;
