import { useState, useEffect, useCallback, useRef } from 'react';

const useWebSocket = (url) => {
  const [status, setStatus] = useState('disconnected');
  const [data, setData] = useState(null);
  const [currentTechnique, setCurrentTechnique] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 2000;

  const connect = useCallback(() => {
    try {
      // 清除之前的连接
      if (socketRef.current) {
        console.log('Closing existing WebSocket connection before creating a new one');
        socketRef.current.close();
        socketRef.current = null;
      }

      setStatus('connecting');
      console.log('Attempting to connect to WebSocket server:', url);
      
      const socket = new WebSocket(url);
      socketRef.current = socket;
      
      socket.onopen = () => {
        console.log('WebSocket connection established');
        setStatus('connected');
        reconnectAttemptsRef.current = 0;
        
        // Clear any reconnect timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      socket.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          console.log('Received WebSocket data:', parsedData);
          
          if (parsedData.type === 'technique_change') {
            // Ensure currentTechnique is always a string
            let techniqueValue = parsedData.technique;
            if (typeof techniqueValue === 'object' && techniqueValue !== null && techniqueValue.hasOwnProperty('text')) {
              techniqueValue = techniqueValue.text;
            } else if (typeof techniqueValue !== 'string') {
              // Fallback if it's not a string or the expected object structure
              console.warn('Received unexpected technique format:', parsedData.technique);
              techniqueValue = String(techniqueValue); // Convert to string as a fallback
            }
            setCurrentTechnique(techniqueValue);
          }
          
          // 确保每次都是一个新对象引用，以触发状态变化检测
          setData({...parsedData, timestamp: new Date().getTime()});
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      socket.onclose = (event) => {
        console.log('WebSocket connection closed', event.code, event.reason);
        setStatus('disconnected');
        
        // 只有在非正常关闭时才尝试重连
        if (event.code !== 1000 && event.code !== 1001) {
          scheduleReconnect();
        }
      };
      
      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setStatus('disconnected');
        
        // 不要在这里调用 socket.close()，因为 onclose 会处理重连
        // 错误已经发生，连接可能已经断开
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setStatus('disconnected');
      scheduleReconnect();
    }
  }, [url]);

  const scheduleReconnect = useCallback(() => {
    // 如果已经安排了重连，不要重复安排
    if (reconnectTimeoutRef.current) {
      return;
    }
    
    // 检查重连尝试次数
    if (reconnectAttemptsRef.current < maxReconnectAttempts) {
      console.log(`Scheduling reconnect attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts} in ${reconnectDelay}ms`);
      reconnectAttemptsRef.current += 1;
      
      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectTimeoutRef.current = null;
        console.log('Attempting to reconnect...');
        connect();
      }, reconnectDelay);
    } else {
      console.log('Maximum reconnect attempts reached');
    }
  }, [connect]);

  const disconnect = useCallback(() => {
    console.log('Manual disconnect requested');
    
    if (socketRef.current) {
      console.log('Closing WebSocket connection');
      socketRef.current.close(1000, 'User requested disconnect');
      socketRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      console.log('Clearing reconnect timeout');
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setStatus('disconnected');
    reconnectAttemptsRef.current = 0;
  }, []);

  // Auto-connect on mount or url change
  useEffect(() => {
    console.log('useWebSocket hook mounted or url changed, connecting to:', url);
    connect();
    
    // Cleanup on unmount or url change
    return () => {
      console.log('useWebSocket hook unmounting or url changing, disconnecting');
      disconnect();
    };
  }, [url, connect, disconnect]);

  return {
    status,
    data,
    currentTechnique,
    connect,
    disconnect
  };
};

export default useWebSocket;
