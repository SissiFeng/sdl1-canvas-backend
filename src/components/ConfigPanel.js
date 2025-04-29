import React, { useState } from 'react';
import { Card, Typography, Divider, Collapse, Form, Input, InputNumber, Select, Button, Space } from 'antd';
import { PlusOutlined, PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Panel } = Collapse;
const { Option } = Select;

// Technique module components
const CVModule = ({ onDragStart }) => (
  <Card 
    size="small" 
    title="Cyclic Voltammetry (CV)" 
    className="draggable-module"
    draggable
    onDragStart={onDragStart}
  >
    <Text>Voltage vs. Current</Text>
  </Card>
);

const PEISModule = ({ onDragStart }) => (
  <Card 
    size="small" 
    title="Impedance Spectroscopy (PEIS)" 
    className="draggable-module"
    draggable
    onDragStart={onDragStart}
  >
    <Text>Frequency Response</Text>
  </Card>
);

const OCVModule = ({ onDragStart }) => (
  <Card 
    size="small" 
    title="Open Circuit Voltage (OCV)" 
    className="draggable-module"
    draggable
    onDragStart={onDragStart}
  >
    <Text>Voltage vs. Time</Text>
  </Card>
);

const CPModule = ({ onDragStart }) => (
  <Card 
    size="small" 
    title="Chronopotentiometry (CP)" 
    className="draggable-module"
    draggable
    onDragStart={onDragStart}
  >
    <Text>Current Control</Text>
  </Card>
);

const LPModule = ({ onDragStart }) => (
  <Card 
    size="small" 
    title="Linear Polarization (LP)" 
    className="draggable-module"
    draggable
    onDragStart={onDragStart}
  >
    <Text>Linear Voltage Sweep</Text>
  </Card>
);

// Configuration forms for each technique
const CVConfigForm = () => (
  <Form layout="vertical">
    <Form.Item label="Voltage Range (V)">
      <Space>
        <InputNumber placeholder="Min" style={{ width: 100 }} defaultValue={-0.5} />
        <InputNumber placeholder="Max" style={{ width: 100 }} defaultValue={0.5} />
      </Space>
    </Form.Item>
    <Form.Item label="Scan Rate (V/s)">
      <InputNumber style={{ width: 200 }} defaultValue={0.05} />
    </Form.Item>
    <Form.Item label="Cycles">
      <InputNumber style={{ width: 200 }} defaultValue={3} />
    </Form.Item>
    <Form.Item label="Record Interval (V)">
      <InputNumber style={{ width: 200 }} defaultValue={0.001} />
    </Form.Item>
    <Form.Item>
      <Button type="primary" icon={<PlayCircleOutlined />}>Run</Button>
    </Form.Item>
  </Form>
);

const PEISConfigForm = () => (
  <Form layout="vertical">
    <Form.Item label="Frequency Range (Hz)">
      <Space>
        <InputNumber placeholder="Min" style={{ width: 100 }} defaultValue={0.1} />
        <InputNumber placeholder="Max" style={{ width: 100 }} defaultValue={100000} />
      </Space>
    </Form.Item>
    <Form.Item label="Amplitude (V)">
      <InputNumber style={{ width: 200 }} defaultValue={0.01} />
    </Form.Item>
    <Form.Item label="Points">
      <InputNumber style={{ width: 200 }} defaultValue={50} />
    </Form.Item>
    <Form.Item label="Sweep Type">
      <Select defaultValue="logarithmic" style={{ width: 200 }}>
        <Option value="logarithmic">Logarithmic</Option>
        <Option value="linear">Linear</Option>
      </Select>
    </Form.Item>
    <Form.Item>
      <Button type="primary" icon={<PlayCircleOutlined />}>Run</Button>
    </Form.Item>
  </Form>
);

const OCVConfigForm = () => (
  <Form layout="vertical">
    <Form.Item label="Duration (s)">
      <InputNumber style={{ width: 200 }} defaultValue={60} />
    </Form.Item>
    <Form.Item label="Record Interval (s)">
      <InputNumber style={{ width: 200 }} defaultValue={0.1} />
    </Form.Item>
    <Form.Item>
      <Button type="primary" icon={<PlayCircleOutlined />}>Run</Button>
    </Form.Item>
  </Form>
);

const CPConfigForm = () => (
  <Form layout="vertical">
    <Form.Item label="Current (A)">
      <InputNumber style={{ width: 200 }} defaultValue={0.001} />
    </Form.Item>
    <Form.Item label="Duration (s)">
      <InputNumber style={{ width: 200 }} defaultValue={30} />
    </Form.Item>
    <Form.Item label="Record Interval (s)">
      <InputNumber style={{ width: 200 }} defaultValue={0.1} />
    </Form.Item>
    <Form.Item>
      <Button type="primary" icon={<PlayCircleOutlined />}>Run</Button>
    </Form.Item>
  </Form>
);

const LPConfigForm = () => (
  <Form layout="vertical">
    <Form.Item label="Voltage Step (V)">
      <InputNumber style={{ width: 200 }} defaultValue={0.01} />
    </Form.Item>
    <Form.Item label="Scan Rate (V/s)">
      <InputNumber style={{ width: 200 }} defaultValue={0.001} />
    </Form.Item>
    <Form.Item label="Record Interval (V)">
      <InputNumber style={{ width: 200 }} defaultValue={0.0001} />
    </Form.Item>
    <Form.Item>
      <Button type="primary" icon={<PlayCircleOutlined />}>Run</Button>
    </Form.Item>
  </Form>
);

const ConfigPanel = ({ visible, onClose, currentTechnique }) => {
  const [activeKey, setActiveKey] = useState(['1', '2']);
  const [selectedTechnique, setSelectedTechnique] = useState(null);

  const handleDragStart = (technique) => (event) => {
    event.dataTransfer.setData('technique', technique);
    setSelectedTechnique(technique);
  };

  const renderConfigForm = () => {
    switch (selectedTechnique) {
      case 'cv':
        return <CVConfigForm />;
      case 'peis':
        return <PEISConfigForm />;
      case 'ocv':
        return <OCVConfigForm />;
      case 'cp':
        return <CPConfigForm />;
      case 'lp':
        return <LPConfigForm />;
      default:
        return (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Text type="secondary">Drag a technique module here to configure</Text>
          </div>
        );
    }
  };

  if (!visible) return null;

  return (
    <div className="config-panel">
      <Title level={4}>Configuration</Title>
      <Divider />
      
      <Collapse 
        activeKey={activeKey} 
        onChange={setActiveKey}
        ghost
      >
        <Panel header="Technique Modules" key="1">
          <Space direction="vertical" style={{ width: '100%' }}>
            <CVModule onDragStart={handleDragStart('cv')} />
            <PEISModule onDragStart={handleDragStart('peis')} />
            <OCVModule onDragStart={handleDragStart('ocv')} />
            <CPModule onDragStart={handleDragStart('cp')} />
            <LPModule onDragStart={handleDragStart('lp')} />
          </Space>
        </Panel>
        
        <Panel header="Parameters" key="2">
          {renderConfigForm()}
        </Panel>
        
        <Panel header="Dimension Mapping" key="3">
          <Form layout="vertical">
            <Form.Item label="X-Axis">
              <Select defaultValue="voltage" style={{ width: '100%' }}>
                <Option value="voltage">Voltage (V)</Option>
                <Option value="current">Current (A)</Option>
                <Option value="time">Time (s)</Option>
                <Option value="frequency">Frequency (Hz)</Option>
                <Option value="re_z">Re(Z) (Ω)</Option>
              </Select>
            </Form.Item>
            <Form.Item label="Y-Axis">
              <Select defaultValue="current" style={{ width: '100%' }}>
                <Option value="voltage">Voltage (V)</Option>
                <Option value="current">Current (A)</Option>
                <Option value="time">Time (s)</Option>
                <Option value="im_z">-Im(Z) (Ω)</Option>
              </Select>
            </Form.Item>
          </Form>
        </Panel>
      </Collapse>
    </div>
  );
};

export default ConfigPanel;
