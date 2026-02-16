/**
 * Live Console Component
 * Scrolling console-style panel for real-time messages
 */
import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';
import { ScrollArea } from '../ui/scroll-area';

const AGENT_COLORS = {
  system: 'text-cyan-400',
  planner: 'text-violet-400',
  executor: 'text-amber-400',
  critic: 'text-emerald-400'
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
              <div key={idx} className="flex gap-3">
                <span className="text-slate-600 flex-shrink-0">
                  {formatTime(msg.timestamp)}
                </span>
                <span className={`font-medium flex-shrink-0 w-20 ${AGENT_COLORS[msg.agent] || 'text-slate-400'}`}>
                  [{msg.agent}]
                </span>
                <span className="text-slate-300 break-all">
                  {msg.message}
                </span>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

export default LiveConsole;
