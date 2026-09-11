import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import { scadaAudio } from '../utils/audioAlert';
import { useAuth } from './AuthContext';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const { token } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [latestReading, setLatestReading] = useState(null);
  const [latestAnomaly, setLatestAnomaly] = useState(null);
  const [latestAlert, setLatestAlert] = useState(null);
  const [liveStream, setLiveStream] = useState([]);
  const [notification, setNotification] = useState(null);

  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const listenersRef = useRef(new Set());

  const addListener = useCallback((cb) => {
    listenersRef.current.add(cb);
    return () => listenersRef.current.delete(cb);
  }, []);

  const connect = useCallback(() => {
    if (!token) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    // Determine WS protocol and host
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Use backend port 8000 if running on Vite port 5173 / 3000
    const host = window.location.hostname;
    const wsUrl = `${wsProtocol}//${host}:8000/ws/sensor-data?token=${encodeURIComponent(token)}`;

    try {
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[WebSocket] Connected to industrial telemetry broker with authenticated session.');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const { event: eventType, data } = payload;

          if (eventType === 'NEW_READING') {
            setLatestReading(data);
            setLiveStream((prev) => [data, ...prev.slice(0, 49)]);
          } else if (eventType === 'ANOMALY_DETECTED') {
            setLatestAnomaly(data);
            scadaAudio.triggerCriticalAlarm();
            setNotification({
              id: Date.now(),
              type: 'CRITICAL',
              title: `Anomaly Flagged on ${data.device_id}`,
              message: data.reason || `Isolation Forest score ${data.anomaly_score} triggered outlier detection.`,
              timestamp: new Date().toLocaleTimeString(),
            });
          } else if (eventType === 'ALERT_GENERATED') {
            setLatestAlert(data);
          }

          // Trigger subscribers
          listenersRef.current.forEach((cb) => cb(eventType, data));
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        // Code 1008 is Policy Violation (invalid/expired JWT) -> halt retry until valid login
        if (event.code === 1008) {
          console.warn('[WebSocket] Handshake rejected: Policy Violation (1008). Invalid or missing JWT.');
          return;
        }
        // Automatic reconnection backoff
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.onerror = (err) => {
        console.warn('[WebSocket] Connection warning, retrying...');
        ws.close();
      };
    } catch (e) {
      console.error('[WebSocket] Init error:', e);
      reconnectTimeoutRef.current = setTimeout(connect, 4000);
    }
  }, [token]);

  useEffect(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    if (token) {
      connect();
    } else {
      setIsConnected(false);
    }
    return () => {
      if (socketRef.current) socketRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [token, connect]);

  const clearNotification = () => setNotification(null);

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        latestReading,
        latestAnomaly,
        latestAlert,
        liveStream,
        notification,
        clearNotification,
        addListener,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
