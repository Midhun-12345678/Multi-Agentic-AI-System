/**
 * Polling hook for job status updates
 * Replaces WebSocket with simple HTTP polling
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { getJobStatus } from '../services/api';

const POLL_INTERVAL = 1000; // 1 second

export function useJobPolling(jobId) {
  const [status, setStatus] = useState(null);
  const [agents, setAgents] = useState({
    planner: { status: 'pending', messages: [] },
    executor: { status: 'pending', messages: [] },
    critic: { status: 'pending', messages: [] }
  });
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const [consoleMessages, setConsoleMessages] = useState([]);
  
  const pollIntervalRef = useRef(null);
  const lastMessageCountRef = useRef({ planner: 0, executor: 0, critic: 0 });
  
  const addConsoleMessage = useCallback((agent, message) => {
    setConsoleMessages(prev => [...prev, {
      timestamp: new Date().toISOString(),
      agent,
      message
    }].slice(-50)); // Keep last 50 messages
  }, []);
  
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);
  
  const pollStatus = useCallback(async () => {
    if (!jobId) return;
    
    try {
      const data = await getJobStatus(jobId);
      
      // Update state
      setStatus(data.status);
      setProgress(data.progress || 0);
      
      // Update agents and detect new messages
      if (data.agents) {
        Object.entries(data.agents).forEach(([name, agent]) => {
          const messages = agent.messages || [];
          const lastCount = lastMessageCountRef.current[name] || 0;
          
          // Add new messages to console
          messages.slice(lastCount).forEach(msg => {
            addConsoleMessage(name, msg.message);
          });
          
          lastMessageCountRef.current[name] = messages.length;
        });
        
        setAgents(data.agents);
      }
      
      // Check if job is complete or errored
      if (data.status === 'complete') {
        setResult(data.result);
        addConsoleMessage('system', '✅ Optimization complete!');
        stopPolling();
      } else if (data.status === 'error') {
        setError(data.error);
        addConsoleMessage('system', `❌ Error: ${data.error}`);
        stopPolling();
      }
      
    } catch (err) {
      console.error('Polling error:', err);
      // Don't stop polling on transient errors, but track 404s
      if (err.response?.status === 404) {
        setError('Job not found');
        stopPolling();
      }
    }
  }, [jobId, addConsoleMessage, stopPolling]);
  
  // Start polling when jobId changes
  useEffect(() => {
    if (jobId) {
      // Reset state for new job
      setStatus(null);
      setAgents({
        planner: { status: 'pending', messages: [] },
        executor: { status: 'pending', messages: [] },
        critic: { status: 'pending', messages: [] }
      });
      setProgress(0);
      setResult(null);
      setError(null);
      setConsoleMessages([]);
      lastMessageCountRef.current = { planner: 0, executor: 0, critic: 0 };
      
      setIsPolling(true);
      addConsoleMessage('system', 'Connected to optimization pipeline');
      
      // Initial poll immediately
      pollStatus();
      
      // Set up interval
      pollIntervalRef.current = setInterval(pollStatus, POLL_INTERVAL);
    }
    
    return () => {
      stopPolling();
    };
  }, [jobId, pollStatus, stopPolling, addConsoleMessage]);
  
  return {
    status,
    agents,
    progress,
    result,
    error,
    isConnected: isPolling, // Keep same API for compatibility
    consoleMessages,
    disconnect: stopPolling
  };
}

export default useJobPolling;
