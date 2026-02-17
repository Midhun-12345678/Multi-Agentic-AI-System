/**
 * AI Resume Optimizer
 * Main Application Component
 */
import React, { useState, useCallback } from 'react';
import { Sparkles, ArrowLeft, Wifi, WifiOff } from 'lucide-react';
import { Button } from './components/ui/button';
import { Progress } from './components/ui/progress';
import { UploadPanel } from './components/resume/UploadPanel';
import { AgentTimeline } from './components/resume/AgentTimeline';
import { LiveConsole } from './components/resume/LiveConsole';
import { ResumePreview } from './components/resume/ResumePreview';
import { ResultSummary } from './components/resume/ResultSummary';
import { ResumeComparison } from './components/resume/ResumeComparison';
import { useJobPolling } from './hooks/useJobPolling';
import { submitOptimization, getJobStatus } from './services/api';
import APP_CONFIG from './config/appConfig';
import './App.css';

// Application states
const STATES = {
  LANDING: 'landing',
  PROCESSING: 'processing',
  RESULTS: 'results'
};

function App() {
  const [appState, setAppState] = useState(STATES.LANDING);
  const [jobId, setJobId] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Polling connection for real-time updates
  const {
    status,
    agents,
    progress,
    result,
    error,
    isConnected,
    consoleMessages,
    disconnect
  } = useJobPolling(jobId);
  
  // Handle form submission
  const handleSubmit = useCallback(async (resumeFile, jobDescription, template) => {
    setIsSubmitting(true);
    setSubmitError(null);
    
    try {
      const response = await submitOptimization(resumeFile, jobDescription, template);
      setJobId(response.job_id);
      setAppState(STATES.PROCESSING);
    } catch (err) {
      console.error('Submission failed:', err);
      setSubmitError(err.response?.data?.detail || 'Failed to submit. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, []);
  
  // Handle state transitions based on job status
  React.useEffect(() => {
    if (status === 'complete' && result) {
      setAppState(STATES.RESULTS);
    } else if (status === 'error') {
      // Keep on processing screen but show error
    }
  }, [status, result]);
  
  // Reset to landing
  const handleReset = () => {
    setAppState(STATES.LANDING);
    setJobId(null);
    setSubmitError(null);
    disconnect();
  };
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
      </div>
      
      {/* Main content */}
      <div className="relative z-10">
        {appState === STATES.LANDING && (
          <LandingScreen 
            onSubmit={handleSubmit}
            isSubmitting={isSubmitting}
            error={submitError}
          />
        )}
        
        {appState === STATES.PROCESSING && (
          <ProcessingScreen
            agents={agents}
            progress={progress}
            consoleMessages={consoleMessages}
            isConnected={isConnected}
            error={error}
            onReset={handleReset}
          />
        )}
        
        {appState === STATES.RESULTS && (
          <ResultsScreen
            result={result}
            onReset={handleReset}
          />
        )}
      </div>
    </div>
  );
}

/**
 * Landing Screen - Upload form
 */
function LandingScreen({ onSubmit, isSubmitting, error }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 mb-6">
            <Sparkles className="w-4 h-4 text-violet-400" />
            <span className="text-sm text-violet-300">Multi-Agent AI System</span>
          </div>
          
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            {APP_CONFIG.landing.headline}
          </h1>
          <p className="text-lg text-slate-400 max-w-md mx-auto">
            {APP_CONFIG.landing.subheadline}
          </p>
        </div>
        
        {/* Upload form */}
        <div className="bg-slate-900/50 backdrop-blur-xl rounded-2xl border border-slate-800 p-8">
          <UploadPanel 
            onSubmit={onSubmit}
            isProcessing={isSubmitting}
          />
          
          {error && (
            <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>
        
        {/* Footer */}
        <p className="text-center text-sm text-slate-600 mt-6">
          Powered by CrewAI • {APP_CONFIG.brand.name}
        </p>
      </div>
    </div>
  );
}

/**
 * Processing Screen - Live AI execution view
 */
function ProcessingScreen({ agents, progress, consoleMessages, isConnected, error, onReset }) {
  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button
            variant="ghost"
            onClick={onReset}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Cancel
          </Button>
          
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-emerald-400">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-amber-400" />
                <span className="text-sm text-amber-400">Reconnecting...</span>
              </>
            )}
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between mb-2">
            <span className="text-sm text-slate-400">Overall Progress</span>
            <span className="text-sm text-violet-400">{progress}%</span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
        
        {/* Main content grid */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Left: Agent Timeline */}
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-white">
              AI Agents at Work
            </h2>
            <AgentTimeline agents={agents} />
          </div>
          
          {/* Right: Live Console */}
          <div className="h-[500px]">
            <h2 className="text-lg font-semibold text-white mb-4">
              Processing Log
            </h2>
            <LiveConsole messages={consoleMessages} />
          </div>
        </div>
        
        {/* Error display */}
        {error && (
          <div className="mt-8 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
            <p className="font-medium">Processing Error</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Results Screen - Final output view
 */
function ResultsScreen({ result, onReset }) {
  const [activeTab, setActiveTab] = React.useState('comparison');
  
  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Button
            variant="ghost"
            onClick={onReset}
            className="text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Optimize Another Resume
          </Button>
          
          <div className="flex items-center gap-2 text-emerald-400">
            <Sparkles className="w-5 h-5" />
            <span className="font-medium">Optimization Complete!</span>
          </div>
        </div>
        
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('comparison')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'comparison'
                ? 'bg-violet-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Before / After Comparison
          </button>
          <button
            onClick={() => setActiveTab('preview')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'preview'
                ? 'bg-violet-500 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            Resume Preview
          </button>
        </div>
        
        {/* Tab Content */}
        {activeTab === 'comparison' ? (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Left: Result Summary */}
            <div className="lg:col-span-1 space-y-6">
              <h2 className="text-lg font-semibold text-white">
                Results Summary
              </h2>
              <ResultSummary result={result} />
            </div>
            
            {/* Right: ATS Comparison */}
            <div className="lg:col-span-2">
              <h2 className="text-lg font-semibold text-white mb-4">
                ATS Keyword Analysis
              </h2>
              <ResumeComparison 
                atsAnalysis={result?.ats_analysis}
                originalResume={result?.original_resume}
                optimizedResume={result?.optimized_resume}
              />
            </div>
          </div>
        ) : (
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Left: Result Summary */}
            <div className="lg:col-span-1 space-y-6">
              <h2 className="text-lg font-semibold text-white">
                Results Summary
              </h2>
              <ResultSummary result={result} />
            </div>
            
            {/* Right: Resume Preview */}
            <div className="lg:col-span-2 h-[800px]">
              <h2 className="text-lg font-semibold text-white mb-4">
                Optimized Resume Preview
              </h2>
              <ResumePreview data={result} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
