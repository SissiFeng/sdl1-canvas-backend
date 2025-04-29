import React from 'react';
import { Button, Space, Typography, Tooltip } from 'antd';
import { 
  ReloadOutlined, 
  ExportOutlined, 
  ApiOutlined, 
  DisconnectOutlined 
} from '@ant-design/icons';

const { Title } = Typography;

const TopNavBar = ({ 
  connectionStatus, 
  onConnect, 
  onDisconnect, 
  onExport, 
  onReset 
}) => {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
      <Title level={3} style={{ margin: 0 }}>Biologic Real-time Data Visualization</Title>
      
      <Space>
        <div className="connection-status">
          <div 
            className={`status-indicator status-${connectionStatus}`} 
          />
          <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}</span>
        </div>
        
        {connectionStatus === 'connected' ? (
          <Tooltip title="Disconnect">
            <Button 
              icon={<DisconnectOutlined />} 
              onClick={onDisconnect}
              danger
            />
          </Tooltip>
        ) : (
          <Tooltip title="Connect">
            <Button 
              icon={<ApiOutlined />} 
              onClick={onConnect}
              type="primary"
            />
          </Tooltip>
        )}
        
        <Tooltip title="Reset">
          <Button 
            icon={<ReloadOutlined />} 
            onClick={onReset}
          />
        </Tooltip>
        
        <Tooltip title="Export Data">
          <Button 
            icon={<ExportOutlined />} 
            onClick={onExport}
          />
        </Tooltip>
      </Space>
    </div>
  );
};

export default TopNavBar;
