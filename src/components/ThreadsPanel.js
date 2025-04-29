import React from 'react';
import { Card, Typography, Empty, Divider } from 'antd';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import Plot from 'react-plotly.js';

const { Title, Text } = Typography;

const ThreadsPanel = ({ threads, currentThread, onThreadSelect, onThreadReorder }) => {
  const handleDragEnd = (result) => {
    if (!result.destination) return;
    onThreadReorder(result);
  };

  return (
    <div style={{ padding: '16px', height: '100%', overflowY: 'auto' }}>
      <Title level={4}>Experiment Threads</Title>
      <Divider />
      
      {threads.length === 0 ? (
        <Empty description="No threads yet" />
      ) : (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="threads">
            {(provided) => (
              <div
                {...provided.droppableProps}
                ref={provided.innerRef}
              >
                {threads.map((thread, index) => (
                  <Draggable key={thread.id} draggableId={`thread-${thread.id}`} index={index}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                      >
                        <Card
                          className={`thread-card ${currentThread && currentThread.id === thread.id ? 'active' : ''}`}
                          onClick={() => onThreadSelect(thread)}
                          hoverable
                          size="small"
                        >
                          <Title level={5}>{thread.title}</Title>
                          <Text type="secondary">{thread.technique}</Text>
                          <div className="thread-thumbnail">
                            {thread.data.x.length > 0 && (
                              <Plot
                                data={[
                                  {
                                    x: thread.data.x,
                                    y: thread.data.y,
                                    type: 'scatter',
                                    mode: 'lines',
                                    line: { width: 1 }
                                  }
                                ]}
                                layout={{
                                  autosize: true,
                                  margin: { l: 20, r: 20, t: 20, b: 20 },
                                  showlegend: false,
                                  xaxis: { showticklabels: false },
                                  yaxis: { showticklabels: false }
                                }}
                                config={{ displayModeBar: false }}
                                style={{ width: '100%', height: '100%' }}
                              />
                            )}
                          </div>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {new Date(thread.timestamp).toLocaleString()}
                          </Text>
                        </Card>
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      )}
    </div>
  );
};

export default ThreadsPanel;
