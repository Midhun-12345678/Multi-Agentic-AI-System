/**
 * Agent Timeline Component
 * Shows vertical timeline of agent processing with live status
 */
import React from 'react';
import { Brain, Cog, ShieldCheck, Check, Loader2, Clock } from 'lucide-react';
import APP_CONFIG from '../../config/appConfig';

const AGENT_ICONS = {
  planner: Brain,
  executor: Cog,
  critic: ShieldCheck
};

const STATUS_STYLES = {
  pending: {
    container: 'border-slate-700 bg-slate-900/30',
    icon: 'text-slate-600',
    text: 'text-slate-500',
    indicator: 'bg-slate-700'
  },
  running: {
    container: 'border-violet-500/50 bg-violet-500/10 shadow-lg shadow-violet-500/10',
    icon: 'text-violet-400',
    text: 'text-violet-300',
    indicator: 'bg-violet-500 animate-pulse'
  },
  complete: {
    container: 'border-emerald-500/30 bg-emerald-500/5',
    icon: 'text-emerald-400',
    text: 'text-emerald-300',
    indicator: 'bg-emerald-500'
  },
  error: {
    container: 'border-red-500/30 bg-red-500/5',
    icon: 'text-red-400',
    text: 'text-red-300',
    indicator: 'bg-red-500'
  }
};

function AgentCard({ name, status, messages }) {
  const config = APP_CONFIG.agents[name];
  const Icon = AGENT_ICONS[name];
  const styles = STATUS_STYLES[status] || STATUS_STYLES.pending;
  
  // Get last 3 messages
  const recentMessages = (messages || []).slice(-3);
  
  return (
    <div 
      data-testid={`agent-${name}`}
      className={`
        relative p-5 rounded-xl border transition-all duration-500
        ${styles.container}
      `}
    >
      {/* Status indicator dot */}
      <div className={`absolute -left-2 top-1/2 -translate-y-1/2 w-3 h-3 rounded-full ${styles.indicator}`} />
      
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className={`p-3 rounded-lg bg-slate-800/50 ${styles.icon}`}>
          {status === 'running' ? (
            <Loader2 className="w-6 h-6 animate-spin" />
          ) : status === 'complete' ? (
            <Check className="w-6 h-6" />
          ) : (
            <Icon className="w-6 h-6" />
          )}
        </div>
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className={`font-semibold ${styles.text}`}>
              {config?.name || name}
            </h3>
            <StatusBadge status={status} />
          </div>
          
          <p className="text-sm text-slate-500 mt-1">
            {config?.description}
          </p>
          
          {/* Recent messages */}
          {recentMessages.length > 0 && (
            <div className="mt-3 space-y-1">
              {recentMessages.map((msg, idx) => (
                <p 
                  key={idx}
                  className={`text-sm ${styles.text} opacity-80 truncate`}
                >
                  {msg.message}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const labels = {
    pending: 'Waiting',
    running: 'Processing',
    complete: 'Complete',
    error: 'Error'
  };
  
  const styles = {
    pending: 'bg-slate-800 text-slate-400',
    running: 'bg-violet-500/20 text-violet-300',
    complete: 'bg-emerald-500/20 text-emerald-300',
    error: 'bg-red-500/20 text-red-300'
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
      {labels[status]}
    </span>
  );
}

export function AgentTimeline({ agents }) {
  const agentOrder = ['planner', 'executor', 'critic'];
  
  return (
    <div data-testid="agent-timeline" className="relative">
      {/* Vertical line connector */}
      <div className="absolute left-[1px] top-0 bottom-0 w-0.5 bg-gradient-to-b from-violet-500/50 via-purple-500/30 to-slate-700/30" />
      
      <div className="space-y-4 pl-6">
        {agentOrder.map((name) => (
          <AgentCard
            key={name}
            name={name}
            status={agents[name]?.status || 'pending'}
            messages={agents[name]?.messages || []}
          />
        ))}
      </div>
    </div>
  );
}

export default AgentTimeline;
