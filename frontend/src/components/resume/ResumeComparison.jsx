/**
 * Resume Comparison Component
 * Side-by-side comparison of original vs optimized resume with ATS scores
 */
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Check, X, TrendingUp, Sparkles } from 'lucide-react';

// Progress Bar Component
function ProgressBar({ value, max = 100, color = "emerald", label, showValue = true }) {
  const percentage = Math.min((value / max) * 100, 100);
  
  const colorClasses = {
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    red: "bg-red-500",
    violet: "bg-violet-500",
    slate: "bg-slate-500"
  };
  
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm text-slate-400">{label}</span>
          {showValue && <span className="text-sm font-medium text-slate-300">{Math.round(value)}%</span>}
        </div>
      )}
      <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${colorClasses[color]} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Keyword Badge Component
function KeywordBadge({ keyword, matched, isNew }) {
  return (
    <span className={`
      inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium
      ${matched 
        ? isNew 
          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
          : 'bg-slate-600/50 text-slate-300'
        : 'bg-red-500/20 text-red-300 border border-red-500/30'
      }
    `}>
      {matched ? <Check className="w-3 h-3" /> : <X className="w-3 h-3" />}
      {keyword}
      {isNew && <Sparkles className="w-3 h-3 text-emerald-400" />}
    </span>
  );
}

// Score Card Component
function ScoreCard({ title, score, subtitle, isOptimized }) {
  const getScoreColor = (s) => {
    if (s >= 80) return 'text-emerald-400';
    if (s >= 60) return 'text-amber-400';
    return 'text-red-400';
  };
  
  return (
    <div className={`
      p-6 rounded-xl text-center
      ${isOptimized 
        ? 'bg-gradient-to-br from-emerald-500/20 to-violet-500/10 border border-emerald-500/30' 
        : 'bg-slate-800/50 border border-slate-700'
      }
    `}>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <div className={`text-5xl font-bold ${getScoreColor(score)}`}>
        {Math.round(score)}%
      </div>
      <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
    </div>
  );
}

export function ResumeComparison({ atsAnalysis, originalResume, optimizedResume }) {
  const [showFullText, setShowFullText] = useState(false);
  const [activeTab, setActiveTab] = useState('comparison'); // 'comparison' or 'keywords'
  
  if (!atsAnalysis) return null;
  
  const { original, optimized, improvement, job_keywords, summary } = atsAnalysis;
  
  return (
    <div className="space-y-6">
      {/* Header with Improvement */}
      <div className="text-center p-6 rounded-xl bg-gradient-to-r from-violet-500/20 via-purple-500/20 to-emerald-500/20 border border-violet-500/30">
        <div className="flex items-center justify-center gap-2 mb-2">
          <TrendingUp className="w-6 h-6 text-emerald-400" />
          <span className="text-2xl font-bold text-emerald-400">
            +{improvement?.score_change || 0}%
          </span>
          <span className="text-slate-400">ATS Score Improvement</span>
        </div>
        <p className="text-sm text-slate-500">
          {improvement?.keywords_added_count || 0} new keywords added to your resume
        </p>
      </div>
      
      {/* Score Comparison */}
      <div className="grid grid-cols-2 gap-4">
        <ScoreCard 
          title="Original Resume"
          score={original?.score || 0}
          subtitle="Before optimization"
          isOptimized={false}
        />
        <ScoreCard 
          title="Optimized Resume"
          score={optimized?.score || 0}
          subtitle="After optimization"
          isOptimized={true}
        />
      </div>
      
      {/* Progress Bars Comparison */}
      <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700 space-y-4">
        <h4 className="font-medium text-slate-300 mb-3">Score Breakdown</h4>
        
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Technical Skills Match</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <ProgressBar 
                value={original?.breakdown?.technical?.score || 0} 
                color="slate" 
                showValue={true}
              />
              <ProgressBar 
                value={optimized?.breakdown?.technical?.score || 0} 
                color="emerald"
                showValue={true}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>Original</span>
              <span>Optimized</span>
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-slate-400">Soft Skills Match</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <ProgressBar 
                value={original?.breakdown?.soft_skills?.score || 0} 
                color="slate"
                showValue={true}
              />
              <ProgressBar 
                value={optimized?.breakdown?.soft_skills?.score || 0} 
                color="violet"
                showValue={true}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-500 mt-1">
              <span>Original</span>
              <span>Optimized</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Keywords Analysis */}
      <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700">
        <h4 className="font-medium text-slate-300 mb-3">Keyword Analysis</h4>
        
        {/* Newly Added Keywords */}
        {improvement?.newly_added_keywords?.length > 0 && (
          <div className="mb-4">
            <p className="text-sm text-emerald-400 mb-2 flex items-center gap-1">
              <Sparkles className="w-4 h-4" />
              Newly Added Keywords ({improvement.newly_added_keywords.length})
            </p>
            <div className="flex flex-wrap gap-2">
              {improvement.newly_added_keywords.map((kw, i) => (
                <KeywordBadge key={i} keyword={kw} matched={true} isNew={true} />
              ))}
            </div>
          </div>
        )}
        
        {/* Matched Keywords */}
        <div className="mb-4">
          <p className="text-sm text-slate-400 mb-2">
            All Matched Keywords ({optimized?.matched?.length || 0})
          </p>
          <div className="flex flex-wrap gap-2">
            {optimized?.matched?.map((kw, i) => (
              <KeywordBadge 
                key={i} 
                keyword={kw} 
                matched={true} 
                isNew={improvement?.newly_added_keywords?.includes(kw)}
              />
            ))}
          </div>
        </div>
        
        {/* Still Missing */}
        {improvement?.still_missing?.length > 0 && (
          <div>
            <p className="text-sm text-red-400 mb-2">
              Still Missing ({improvement.still_missing.length})
            </p>
            <div className="flex flex-wrap gap-2">
              {improvement.still_missing.slice(0, 10).map((kw, i) => (
                <KeywordBadge key={i} keyword={kw} matched={false} isNew={false} />
              ))}
              {improvement.still_missing.length > 10 && (
                <span className="text-xs text-slate-500">
                  +{improvement.still_missing.length - 10} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Side-by-Side Resume Text */}
      <div className="rounded-xl bg-slate-800/50 border border-slate-700 overflow-hidden">
        <button
          onClick={() => setShowFullText(!showFullText)}
          className="w-full p-4 flex items-center justify-between hover:bg-slate-700/50 transition-colors"
        >
          <span className="font-medium text-slate-300">
            Side-by-Side Resume Comparison
          </span>
          {showFullText ? (
            <ChevronUp className="w-5 h-5 text-slate-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-slate-400" />
          )}
        </button>
        
        {showFullText && (
          <div className="grid grid-cols-2 divide-x divide-slate-700">
            {/* Original Resume */}
            <div className="p-4">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-700">
                <div className="w-3 h-3 rounded-full bg-slate-500" />
                <span className="text-sm font-medium text-slate-400">Original Resume</span>
              </div>
              <pre className="text-xs text-slate-400 whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                {originalResume || "Original resume text not available"}
              </pre>
            </div>
            
            {/* Optimized Resume */}
            <div className="p-4 bg-emerald-500/5">
              <div className="flex items-center gap-2 mb-3 pb-2 border-b border-emerald-500/30">
                <div className="w-3 h-3 rounded-full bg-emerald-500" />
                <span className="text-sm font-medium text-emerald-400">Optimized Resume</span>
              </div>
              <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                {optimizedResume || "Optimized resume text not available"}
              </pre>
            </div>
          </div>
        )}
      </div>
      
      {/* Job Keywords Reference */}
      <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700">
        <h4 className="font-medium text-slate-300 mb-3">
          Keywords Extracted from Job Description
        </h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-violet-400 mb-2">Technical ({job_keywords?.technical?.length || 0})</p>
            <div className="flex flex-wrap gap-1">
              {job_keywords?.technical?.map((kw, i) => (
                <span key={i} className="px-2 py-0.5 bg-violet-500/20 text-violet-300 rounded text-xs">
                  {kw}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm text-amber-400 mb-2">Soft Skills ({job_keywords?.soft_skills?.length || 0})</p>
            <div className="flex flex-wrap gap-1">
              {job_keywords?.soft_skills?.map((kw, i) => (
                <span key={i} className="px-2 py-0.5 bg-amber-500/20 text-amber-300 rounded text-xs">
                  {kw}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResumeComparison;
