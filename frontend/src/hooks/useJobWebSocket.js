/**
 * WebSocket hook for real-time job updates
 */
import { useState, useEffect, useCallback, useRef } from 'react';

const WS_BASE_URL = process.env.REACT_APP_BACKEND_URL?.replace('https://', 'wss://').replace('http://', 'ws://') || 'ws://localhost:8001';

export function useJobWebSocket(jobId) {
  const [status, setStatus] = useState(null);
  const [agents, setAgents] = useState({
    planner: { status: 'pending', messages: [] },
    executor: { status: 'pending', messages: [] },
    critic: { status: 'pending', messages: [] }
  });
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [consoleMessages, setConsoleMessages] = useState([]);
  
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  const addConsoleMessage = useCallback((agent, message) => {
    setConsoleMessages(prev => [...prev, {
      timestamp: new Date().toISOString(),
      agent,
      message
    }].slice(-50)); // Keep last 50 messages
  }, []);
  
  const connect = useCallback(() => {
    if (!jobId) return;
    
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }
    
    const wsUrl = `${WS_BASE_URL}/api/ws/${jobId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message:', data.type, data);
          
          switch (data.type) {
            case 'initial_status':
              // Initial state from server
              if (data.data) {
                setStatus(data.data.status);
                setProgress(data.data.progress || 0);
                if (data.data.agents) {
                  setAgents(prev => ({
                    ...prev,
                    ...Object.fromEntries(
                      Object.entries(data.data.agents).map(([name, agent]) => [
                        name,
                        { 
                          status: agent.status, 
                          messages: agent.messages || []
                        }
                      ])
                    )
                  }));
                }
                if (data.data.result) {
                  setResult(data.data.result);
                }
                if (data.data.error) {
                  setError(data.data.error);
                }
              }
              break;
              
            case 'connected':
              addConsoleMessage('system', 'Connected to optimization pipeline');
              break;
              
            case 'agent_started':
              setAgents(prev => ({
                ...prev,
                [data.data.agent]: {
                  ...prev[data.data.agent],
                  status: 'running'
                }
              }));
              addConsoleMessage(data.data.agent, `${data.data.agent} started processing...`);
              break;
              
            case 'agent_message':
              setAgents(prev => ({
                ...prev,
                [data.data.agent]: {
                  ...prev[data.data.agent],
                  messages: [...(prev[data.data.agent]?.messages || []), {
                    timestamp: data.timestamp,
                    message: data.data.message
                  }]
                }
              }));
              addConsoleMessage(data.data.agent, data.data.message);
              break;
              
            case 'agent_completed':
              setAgents(prev => ({
                ...prev,
                [data.data.agent]: {
                  ...prev[data.data.agent],
                  status: 'complete'
                }
              }));
              addConsoleMessage(data.data.agent, `${data.data.agent} completed`);
              break;
              
            case 'validation_warning':
              addConsoleMessage('critic', `⚠️ ${data.data.warning}`);
              break;
              
            case 'job_progress':
              setProgress(data.data.progress);
              setStatus(data.data.status);
              break;
              
            case 'job_completed':
              setStatus('complete');
              setProgress(100);
              setResult(data.data.result);
              addConsoleMessage('system', '✅ Optimization complete!');
              break;
              
            case 'job_failed':
              setStatus('error');
              setError(data.data.error);
              addConsoleMessage('system', `❌ Error: ${data.data.error}`);
              break;
              
            default:
              // Handle ping/pong
              if (event.data === 'ping') {
                ws.send('pong');
              }
          }
        } catch (e) {
          // Handle non-JSON messages (ping/pong)
          if (event.data === 'ping') {
            ws.send('pong');
          }
        }
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        
        // Reconnect if not intentionally closed
        if (event.code !== 1000 && status !== 'complete' && status !== 'error') {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 3000);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
      };
      
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
      setError('Failed to connect');
    }
  }, [jobId, status, addConsoleMessage]);
  
  // Connect when jobId changes
  useEffect(() => {
    if (jobId) {
      connect();
    }
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000);
      }
    };
  }, [jobId, connect]);
  
  // Disconnect function
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000);
    }
  }, []);
  
  return {
    status,
    agents,
    progress,
    result,
    error,
    isConnected,
    consoleMessages,
    disconnect
  };
}

export default useJobWebSocket;
