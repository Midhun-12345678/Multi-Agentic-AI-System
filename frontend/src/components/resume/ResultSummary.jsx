/**
 * Result Summary Component
 * Shows ATS score, issues, and download button
 * Enhanced with validation warnings display
 */
import React, { useState } from 'react';
import { Download, AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import APP_CONFIG from '../../config/appConfig';

export function ResultSummary({ result }) {
  const [showSkillsNote, setShowSkillsNote] = useState(false);
  const [showValidationNotes, setShowValidationNotes] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  if (!result) return null;
  
  const { 
    pdf_base64, 
    template_used,
    pre_pdf_validation = {},
    validation = {},
    baseline = {},
    ats_analysis = {},
    validation_warnings = [], // Validation warnings from processing
    judge_scores = null,
    authenticity_warning = false,
    critic_report = {}
  } = result;
  
  // Use ATS score if available, otherwise fall back to data integrity score
  const atsScore = ats_analysis?.summary?.optimized_score;
  const atsImprovement = ats_analysis?.summary?.improvement;
  const score = atsScore || pre_pdf_validation.data_integrity_score || 85;
  const warnings = pre_pdf_validation.warnings || [];
  const fieldMapping = pre_pdf_validation.field_mapping || {};
  
  // Separate critical warnings from informational notes
  const criticalWarnings = validation_warnings.filter(w => 
    w.includes('[CRITICAL]') || w.includes('Missing email') || w.includes('Missing phone')
  );
  const infoWarnings = validation_warnings.filter(w => 
    w.includes('[WARNING]') || w.includes('mismatch') || w.includes('below threshold')
  ).filter(w => !criticalWarnings.includes(w));
  
  const handleDownload = () => {
    if (!pdf_base64) return;
    
    // Convert base64 to blob
    const byteCharacters = atob(pdf_base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: 'application/pdf' });
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `resume_optimized_${template_used || 'professional'}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  const getScoreColor = (s) => {
    if (s >= 90) return 'text-emerald-400';
    if (s >= 70) return 'text-amber-400';
    return 'text-red-400';
  };
  
  const getScoreBg = (s) => {
    if (s >= 90) return 'from-emerald-500/20 to-emerald-500/5';
    if (s >= 70) return 'from-amber-500/20 to-amber-500/5';
    return 'from-red-500/20 to-red-500/5';
  };
  
  return (
    <div data-testid="result-summary" className="space-y-6">
      {/* ATS Score */}
      <div className={`
        p-8 rounded-2xl text-center
        bg-gradient-to-b ${getScoreBg(score)}
        border border-slate-700/50
      `}>
        <p className="text-sm font-medium text-slate-400 mb-2">
          {APP_CONFIG.results.scoreLabel}
        </p>
        <div className={`text-7xl font-bold ${getScoreColor(score)}`}>
          {Math.round(score)}%
        </div>
        <p className="text-slate-500 mt-2">ATS Keyword Match</p>
        {atsImprovement > 0 && (
          <div className="mt-2 inline-flex items-center gap-1 px-3 py-1 bg-emerald-500/20 rounded-full">
            <span className="text-emerald-400 text-sm font-medium">+{Math.round(atsImprovement)}% improvement</span>
          </div>
        )}
      </div>
      
      {/* Field Mapping Status */}
      <div className="grid grid-cols-2 gap-3">
        <FieldStatus 
          label="Experiences" 
          original={fieldMapping.experience_count?.original || baseline.experience_count || 0}
          final={fieldMapping.experience_count?.final || 0}
          match={fieldMapping.experience_count?.match}
        />
        <FieldStatus 
          label="Projects" 
          original={fieldMapping.projects_count?.original || baseline.project_count || 0}
          final={fieldMapping.projects_count?.final || 0}
          match={fieldMapping.projects_count?.match}
        />
      </div>
      
      {/* Critical Warnings */}
      {(warnings.length > 0 || criticalWarnings.length > 0) && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
          <h4 className="flex items-center gap-2 font-medium text-red-400 mb-2">
            <AlertCircle className="w-4 h-4" />
            {APP_CONFIG.results.criticalIssuesLabel}
          </h4>
          <ul className="space-y-1">
            {warnings.map((warning, idx) => (
              <li key={`w-${idx}`} className="text-sm text-red-300/80">
                • {warning}
              </li>
            ))}
            {criticalWarnings.map((warning, idx) => (
              <li key={`cw-${idx}`} className="text-sm text-red-300/80">
                • {warning.replace('[CRITICAL] ', '')}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Validation Notes (non-critical) - Collapsible */}
      {infoWarnings.length > 0 && (
        <>
          <button 
            onClick={() => setShowValidationNotes(!showValidationNotes)}
            className="w-full p-3 rounded-lg bg-amber-500/10 border border-amber-500/30
                       flex items-center justify-between text-sm text-amber-400
                       hover:bg-amber-500/15 transition-colors"
          >
            <span className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Validation Notes ({infoWarnings.length})
            </span>
            {showValidationNotes ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
          
          {showValidationNotes && (
            <div className="p-4 rounded-lg bg-amber-500/5 border border-amber-500/20">
              <p className="text-xs text-slate-500 mb-2">
                Minor adjustments made during optimization (data integrity preserved)
              </p>
              <ul className="space-y-1">
                {infoWarnings.map((warning, idx) => (
                  <li key={idx} className="text-sm text-amber-300/70">
                    • {warning.replace('[WARNING] ', '')}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
      
      {/* Success Message */}
      {warnings.length === 0 && criticalWarnings.length === 0 && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
          <h4 className="flex items-center gap-2 font-medium text-emerald-400">
            <CheckCircle className="w-4 h-4" />
            All fields properly mapped!
          </h4>
        </div>
      )}
      
      {/* Skills Grouping Note */}
      <button 
        onClick={() => setShowSkillsNote(!showSkillsNote)}
        className="w-full p-3 rounded-lg bg-slate-800/50 border border-slate-700/50
                   flex items-center justify-between text-sm text-slate-400
                   hover:bg-slate-800 transition-colors"
      >
        <span className="flex items-center gap-2">
          <Info className="w-4 h-4" />
          Skills grouping explanation
        </span>
        {showSkillsNote ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>
      
      {showSkillsNote && (
        <div className="p-4 rounded-lg bg-slate-800/30 text-sm text-slate-400">
          {APP_CONFIG.results.skillsGroupNote}
        </div>
      )}

      {/* AI Quality Scores Section */}
      {judge_scores && (judge_scores.overall_score > 0 || !judge_scores.error) ? (
        <div className="space-y-4">
          {/* Section Header */}
          <div className="text-center">
            <h3 className="text-lg font-semibold text-slate-200">AI Quality Scores</h3>
            <p className="text-sm text-slate-500">Independent evaluation by a separate AI judge</p>
          </div>

          {/* Overall Quality Score */}
          <div className="p-6 rounded-xl bg-slate-800/50 border border-slate-700/50 text-center">
            <div className="flex items-center justify-center gap-3">
              <span className={`text-5xl font-bold ${
                judge_scores.overall_score >= 85 ? 'text-emerald-400' :
                judge_scores.overall_score >= 70 ? 'text-amber-400' :
                judge_scores.overall_score >= 50 ? 'text-orange-400' :
                'text-red-400'
              }`}>
                {Math.round(judge_scores.overall_score)}
              </span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                judge_scores.overall_score >= 85 ? 'bg-emerald-500/20 text-emerald-400' :
                judge_scores.overall_score >= 70 ? 'bg-amber-500/20 text-amber-400' :
                judge_scores.overall_score >= 50 ? 'bg-orange-500/20 text-orange-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {judge_scores.overall_score >= 85 ? 'Excellent' :
                 judge_scores.overall_score >= 70 ? 'Good' :
                 judge_scores.overall_score >= 50 ? 'Needs Work' :
                 'Poor'}
              </span>
            </div>
          </div>

          {/* Four Score Bars */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-800/30 border border-slate-700/50">
            {[
              { label: 'Keyword Match', score: judge_scores.keyword_match_rate, reasoning: judge_scores.keyword_match_reasoning },
              { label: 'Readability', score: judge_scores.readability_score, reasoning: judge_scores.readability_reasoning },
              { label: 'Authenticity', score: judge_scores.authenticity_score, reasoning: judge_scores.authenticity_reasoning },
              { label: 'ATS Compatibility', score: judge_scores.ats_compatibility_score, reasoning: judge_scores.ats_reasoning }
            ].map(({ label, score, reasoning }) => (
              <div key={label} className="space-y-1">
                <div className="flex items-center gap-3">
                  <span className="text-sm text-slate-400 w-32 flex-shrink-0">{label}</span>
                  <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        score >= 85 ? 'bg-emerald-500' :
                        score >= 70 ? 'bg-amber-500' :
                        score >= 50 ? 'bg-orange-500' :
                        'bg-red-500'
                      }`}
                      style={{ width: `${score || 0}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-slate-300 w-10 text-right">{score || 0}</span>
                </div>
                {reasoning && (
                  <p className="text-xs text-slate-500 italic pl-32">{reasoning}</p>
                )}
              </div>
            ))}
          </div>

          {/* Authenticity Warning Banner */}
          {authenticity_warning && (
            <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
              <p className="text-sm text-yellow-400">
                ⚠️ Authenticity Alert: This resume was flagged by the critic after maximum retries. Review before sending.
              </p>
            </div>
          )}

          {/* Improvement Suggestions - Collapsible */}
          {judge_scores.improvement_suggestions && judge_scores.improvement_suggestions.length > 0 && (
            <>
              <button
                onClick={() => setShowSuggestions(!showSuggestions)}
                className="w-full p-3 rounded-lg bg-slate-800/50 border border-slate-700/50
                           flex items-center justify-between text-sm text-slate-400
                           hover:bg-slate-800 transition-colors"
              >
                <span>{showSuggestions ? 'Hide Improvement Suggestions' : 'Show Improvement Suggestions'}</span>
                {showSuggestions ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
              {showSuggestions && (
                <div className="p-4 rounded-lg bg-slate-800/30 border border-slate-700/50">
                  <ul className="space-y-2">
                    {judge_scores.improvement_suggestions.map((suggestion, idx) => (
                      <li key={idx} className="text-sm text-slate-400">
                        → {suggestion}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>
      ) : judge_scores?.error ? (
        <div className="p-4 rounded-lg bg-slate-800/30 text-sm text-slate-500 text-center">
          Quality evaluation unavailable for this optimization.
        </div>
      ) : null}
      
      {/* Download Button */}
      <Button
        data-testid="download-button"
        onClick={handleDownload}
        disabled={!pdf_base64}
        className="w-full h-14 text-lg font-semibold
                   bg-gradient-to-r from-emerald-600 to-teal-600 
                   hover:from-emerald-500 hover:to-teal-500
                   disabled:opacity-50"
      >
        <Download className="w-5 h-5 mr-2" />
        {APP_CONFIG.results.downloadButton}
      </Button>
    </div>
  );
}

function FieldStatus({ label, original, final, match }) {
  const isMatch = match ?? (final >= original);
  
  return (
    <div className={`
      p-3 rounded-lg border
      ${isMatch 
        ? 'bg-emerald-500/5 border-emerald-500/20' 
        : 'bg-amber-500/5 border-amber-500/20'
      }
    `}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`font-medium ${isMatch ? 'text-emerald-400' : 'text-amber-400'}`}>
        {original} → {final}
        {isMatch ? ' ✓' : ' ⚠'}
      </p>
    </div>
  );
}

export default ResultSummary;
