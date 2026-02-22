/**
 * Live Console Component
 * Scrolling console-style panel for real-time messages
 * Enhanced with severity badges and retry indicators
 */
import React, { useRef, useEffect } from 'react';
import { Terminal, AlertCircle, AlertTriangle, Info, RotateCcw } from 'lucide-react';
import { ScrollArea } from '../ui/scroll-area';

const AGENT_COLORS = {
  system: 'text-cyan-400',
  planner: 'text-violet-400',
  executor: 'text-amber-400',
  critic: 'text-emerald-400'
};

const SEVERITY_STYLES = {
  critical: {
    text: 'text-red-300',
    bg: 'bg-red-500/10',
    icon: AlertCircle,
    iconColor: 'text-red-400'
  },
  warning: {
    text: 'text-amber-300',
    bg: 'bg-amber-500/10',
    icon: AlertTriangle,
    iconColor: 'text-amber-400'
  },
  info: {
    text: 'text-blue-300',
    bg: 'bg-blue-500/10',
    icon: Info,
    iconColor: 'text-blue-400'
  }
};

const MESSAGE_TYPE_STYLES = {
  error: 'text-red-300',
  warning: 'text-amber-300',
  retry: 'text-orange-300',
  progress: 'text-violet-300',
  info: 'text-slate-300'
};

export function LiveConsole({ messages }) {
  const scrollRef = useRef(null);
  
  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);
  
  const formatTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit' 
      });
    } catch {
      return '--:--:--';
    }
  };
  
  const getSeverityIcon = (severity) => {
    if (!severity) return null;
    const style = SEVERITY_STYLES[severity];
    if (!style) return null;
    const Icon = style.icon;
    return <Icon className={`w-3 h-3 ${style.iconColor} flex-shrink-0`} />;
  };
  
  const getMessageStyle = (msg) => {
    // Priority: severity > type > default
    if (msg.severity && SEVERITY_STYLES[msg.severity]) {
      return `${SEVERITY_STYLES[msg.severity].text} ${SEVERITY_STYLES[msg.severity].bg} px-2 py-0.5 rounded`;
    }
    if (msg.type && MESSAGE_TYPE_STYLES[msg.type]) {
      return MESSAGE_TYPE_STYLES[msg.type];
    }
    return 'text-slate-300';
  };
  
  return (
    <div 
      data-testid="live-console"
      className="h-full flex flex-col bg-slate-950 rounded-xl border border-slate-800 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800 bg-slate-900/50">
        <Terminal className="w-4 h-4 text-slate-500" />
        <span className="text-sm font-medium text-slate-400">Live Processing Log</span>
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-slate-500">Live</span>
        </div>
      </div>
      
      {/* Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-2 font-mono text-sm">
          {messages.length === 0 ? (
            <p className="text-slate-600 italic">Waiting for processing to start...</p>
          ) : (
            messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex gap-3 ${msg.severity === 'critical' ? 'bg-red-500/5 -mx-2 px-2 py-1 rounded' : ''}`}
              >
                <span className="text-slate-600 flex-shrink-0">
                  {formatTime(msg.timestamp)}
                </span>
                <span className={`font-medium flex-shrink-0 w-20 ${AGENT_COLORS[msg.agent] || 'text-slate-400'}`}>
                  [{msg.agent}]
                </span>
                <div className="flex items-start gap-2 flex-1">
                  {getSeverityIcon(msg.severity)}
                  {msg.retry_attempt && (
                    <span className="inline-flex items-center gap-0.5 text-orange-400 text-xs">
                      <RotateCcw className="w-3 h-3" />
                      {msg.retry_attempt}
                    </span>
                  )}
                  <span className={`break-all ${getMessageStyle(msg)}`}>
                    {msg.message}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

export default LiveConsole;
