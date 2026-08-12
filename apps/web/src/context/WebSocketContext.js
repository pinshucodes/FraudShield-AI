'use client';

import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

const WebSocketContext = createContext();

export function WebSocketProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef(null);

  useEffect(() => {
    // Determine the WS URL based on the current window location to handle both local and prod
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    
    // During local dev with next proxy, we might need to point to the backend directly if next rewrites don't support ws
    // Next.js rewrites DO support ws, but let's connect directly to the backend proxy path
    // Wait, since we have rewrites in next.config.mjs mapping /api to http://127.0.0.1:8000/api/v1
    // We should connect to the Next.js server which will proxy the websocket.
    const wsUrl = `${protocol}//${host}/api/ws`;

    const connect = () => {
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('WebSocket Connected');
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages((prev) => [data, ...prev].slice(0, 50)); // Keep last 50 messages
        } catch (e) {
          console.error('Error parsing WebSocket message', e);
        }
      };

      ws.current.onclose = () => {
        console.log('WebSocket Disconnected. Reconnecting...');
        setIsConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(connect, 3000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket Error:', error);
        ws.current.close();
      };
    };

    connect();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const sendMessage = (msg) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg));
    }
  };

  return (
    <WebSocketContext.Provider value={{ messages, isConnected, sendMessage }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  return useContext(WebSocketContext);
}
