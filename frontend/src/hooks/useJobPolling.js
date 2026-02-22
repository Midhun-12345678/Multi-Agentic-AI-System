/**
 * Polling hook for job status updates
 * Replaces WebSocket with simple HTTP polling
 * Uses adaptive polling: faster during active processing, slower when idle
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { getJobStatus } from '../services/api';

// Adaptive polling intervals
const POLL_INTERVAL_ACTIVE = 500;   // 500ms when agents are running (fast updates)
const POLL_INTERVAL_IDLE = 2000;    // 2s when waiting/queued (reduce API load)
const POLL_INTERVAL_DEFAULT = 1000; // 1s default

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
  const currentIntervalRef = useRef(POLL_INTERVAL_DEFAULT);
  const pollStatusRef = useRef(null); // Store pollStatus ref for interval updates
  
  const addConsoleMessage = useCallback((agent, message, msgData = {}) => {
    setConsoleMessages(prev => [...prev, {
      timestamp: new Date().toISOString(),
      agent,
      message,
      ...msgData // Include type, severity, retry_attempt if present
    }].slice(-50)); // Keep last 50 messages
  }, []);
  
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);
  
  // Determine optimal polling interval based on current state
  const getPollingInterval = useCallback((agentsData, jobStatus) => {
    // If job is complete or errored, use slow interval (will stop soon anyway)
    if (jobStatus === 'complete' || jobStatus === 'error') {
      return POLL_INTERVAL_IDLE;
    }
    
    // Check if any agent is actively running - use fast polling
    if (agentsData) {
      const hasRunningAgent = Object.values(agentsData).some(
        agent => agent.status === 'running'
      );
      if (hasRunningAgent) {
        return POLL_INTERVAL_ACTIVE;
      }
    }
    
    // Default interval for queued/pending states
    return POLL_INTERVAL_DEFAULT;
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
          
          // Add new messages to console with full metadata
          messages.slice(lastCount).forEach(msg => {
            addConsoleMessage(name, msg.message, {
              type: msg.type,
              severity: msg.severity,
              retry_attempt: msg.retry_attempt
            });
          });
          
          lastMessageCountRef.current[name] = messages.length;
        });
        
        setAgents(data.agents);
        
        // Adaptive polling: adjust interval based on activity
        const optimalInterval = getPollingInterval(data.agents, data.status);
        if (optimalInterval !== currentIntervalRef.current && pollIntervalRef.current) {
          currentIntervalRef.current = optimalInterval;
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = setInterval(() => pollStatusRef.current?.(), optimalInterval);
        }
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
  }, [jobId, addConsoleMessage, stopPolling, getPollingInterval]);
  
  // Keep pollStatusRef updated
  useEffect(() => {
    pollStatusRef.current = pollStatus;
  }, [pollStatus]);
  
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
      currentIntervalRef.current = POLL_INTERVAL_DEFAULT;
      
      setIsPolling(true);
      addConsoleMessage('system', 'Connected to optimization pipeline');
      
      // Initial poll immediately
      pollStatus();
      
      // Set up interval with default rate (will adapt after first poll)
      pollIntervalRef.current = setInterval(() => pollStatusRef.current?.(), POLL_INTERVAL_DEFAULT);
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
