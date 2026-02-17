/**
 * Result Summary Component
 * Shows ATS score, issues, and download button
 */
import React, { useState } from 'react';
import { Download, AlertTriangle, CheckCircle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../ui/button';
import APP_CONFIG from '../../config/appConfig';

export function ResultSummary({ result }) {
  const [showSkillsNote, setShowSkillsNote] = useState(false);
  
  if (!result) return null;
  
  const { 
    pdf_base64, 
    template_used,
    pre_pdf_validation = {},
    validation = {},
    baseline = {},
    ats_analysis = {}
  } = result;
  
  // Use ATS score if available, otherwise fall back to data integrity score
  const atsScore = ats_analysis?.summary?.optimized_score;
  const atsImprovement = ats_analysis?.summary?.improvement;
  const score = atsScore || pre_pdf_validation.data_integrity_score || 85;
  const warnings = pre_pdf_validation.warnings || [];
  const fieldMapping = pre_pdf_validation.field_mapping || {};
  
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
      
      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
          <h4 className="flex items-center gap-2 font-medium text-amber-400 mb-2">
            <AlertTriangle className="w-4 h-4" />
            {APP_CONFIG.results.criticalIssuesLabel}
          </h4>
          <ul className="space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx} className="text-sm text-amber-300/80">
                • {warning}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* Success Message */}
      {warnings.length === 0 && (
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
