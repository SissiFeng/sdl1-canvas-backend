import { useState, useEffect, useCallback, useRef } from 'react';

const useWebSocket = (url) => {
  const [status, setStatus] = useState('disconnected');
  const [data, setData] = useState(null);
  const [currentTechnique, setCurrentTechnique] = useState(null);
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
    }

    setStatus('connecting');
    
    const socket = new WebSocket(url);
    socketRef.current = socket;
    
    socket.onopen = () => {
      console.log('WebSocket connection established');
      setStatus('connected');
      
      // Clear any reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
    
    socket.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        console.log('Received data:', parsedData);
        
        if (parsedData.type === 'technique_change') {
          setCurrentTechnique(parsedData.technique);
        }
        
        setData(parsedData);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    socket.onclose = () => {
      console.log('WebSocket connection closed');
      setStatus('disconnected');
      
      // Schedule reconnect
      if (!reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 2000);
      }
    };
    
    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus('disconnected');
      
      // Close socket and reconnect
      socket.close();
    };
  }, [url]);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setStatus('disconnected');
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    status,
    data,
    currentTechnique,
    connect,
    disconnect
  };
};

export default useWebSocket;
