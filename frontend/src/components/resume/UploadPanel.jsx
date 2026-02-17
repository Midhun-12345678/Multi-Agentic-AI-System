/**
 * Upload Panel Component
 * Resume upload and job description input
 */
import React, { useRef, useState } from 'react';
import { Upload, FileText, Sparkles } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import APP_CONFIG from '../../config/appConfig';

export function UploadPanel({ onSubmit, isProcessing }) {
  const [resumeFile, setResumeFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [template, setTemplate] = useState('harvard');
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type === 'application/pdf') {
        setResumeFile(file);
      }
    }
  };
  
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0]);
    }
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (resumeFile && jobDescription.trim()) {
      onSubmit(resumeFile, jobDescription, template);
    }
  };
  
  const isValid = resumeFile && jobDescription.trim().length > 50;
  
  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Resume Upload */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-slate-300">
          {APP_CONFIG.landing.uploadLabel}
        </label>
        <div
          data-testid="resume-dropzone"
          className={`
            relative border-2 border-dashed rounded-xl p-8 text-center
            transition-all duration-300 cursor-pointer
            ${dragActive 
              ? 'border-violet-500 bg-violet-500/10' 
              : resumeFile 
                ? 'border-emerald-500/50 bg-emerald-500/5' 
                : 'border-slate-700 hover:border-slate-600 bg-slate-900/50'
            }
          `}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
            data-testid="resume-file-input"
          />
          
          {resumeFile ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="w-8 h-8 text-emerald-400" />
              <div className="text-left">
                <p className="font-medium text-emerald-400">{resumeFile.name}</p>
                <p className="text-sm text-slate-500">
                  {(resumeFile.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <Upload className="w-10 h-10 mx-auto text-slate-500" />
              <div>
                <p className="text-slate-300">Drop your resume here or click to browse</p>
                <p className="text-sm text-slate-500">{APP_CONFIG.landing.uploadHint}</p>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Job Description */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-slate-300">
          {APP_CONFIG.landing.jobDescLabel}
        </label>
        <Textarea
          data-testid="job-description-input"
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder={APP_CONFIG.landing.jobDescPlaceholder}
          className="min-h-[200px] bg-slate-900/50 border-slate-700 focus:border-violet-500 
                     text-slate-200 placeholder:text-slate-600 resize-none"
        />
        <p className="text-xs text-slate-500">
          {jobDescription.length} characters • Minimum 50 required
        </p>
      </div>
      
      {/* Template Selection */}
      <div className="space-y-3">
        <label className="text-sm font-medium text-slate-300">
          Resume Template
        </label>
        <Select value={template} onValueChange={setTemplate}>
          <SelectTrigger 
            data-testid="template-select"
            className="bg-slate-900/50 border-slate-700"
          >
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-900 border-slate-700">
            {APP_CONFIG.templates.map((t) => (
              <SelectItem key={t.value} value={t.value}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      
      {/* Submit Button */}
      <Button
        data-testid="submit-button"
        type="submit"
        disabled={!isValid || isProcessing}
        className="w-full h-14 text-lg font-semibold
                   bg-gradient-to-r from-violet-600 to-purple-600 
                   hover:from-violet-500 hover:to-purple-500
                   disabled:opacity-50 disabled:cursor-not-allowed
                   transition-all duration-300"
      >
        {isProcessing ? (
          <>
            <Sparkles className="w-5 h-5 mr-2 animate-pulse" />
            {APP_CONFIG.landing.processingButton}
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5 mr-2" />
            {APP_CONFIG.landing.submitButton}
          </>
        )}
      </Button>
    </form>
  );
}

export default UploadPanel;
