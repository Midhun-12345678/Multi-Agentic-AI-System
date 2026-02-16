/**
 * Resume Preview Component
 * Renders optimized resume visually (not raw JSON)
 */
import React from 'react';
import { User, Mail, Phone, Linkedin, Github, Briefcase, FolderOpen, GraduationCap, Wrench } from 'lucide-react';
import { ScrollArea } from '../ui/scroll-area';

function parseMarkdownBold(text) {
  if (!text) return text;
  // Convert **text** to <strong>text</strong>
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((part, i) => 
    i % 2 === 1 ? <strong key={i} className="text-violet-300">{part}</strong> : part
  );
}

function formatDescription(description) {
  if (!description) return null;
  
  // Split by \n or actual newlines
  const lines = description.split(/\\n|\n/).filter(line => line.trim());
  
  return (
    <ul className="space-y-1.5 mt-2">
      {lines.map((line, idx) => {
        // Remove bullet prefix if present
        const cleanLine = line.replace(/^[-•*]\s*/, '').trim();
        return (
          <li key={idx} className="flex items-start gap-2 text-slate-400 text-sm">
            <span className="text-violet-500 mt-1">•</span>
            <span>{parseMarkdownBold(cleanLine)}</span>
          </li>
        );
      })}
    </ul>
  );
}

export function ResumePreview({ data }) {
  if (!data) return null;
  
  // Parse structured data from executor output or result
  let resumeData = {};
  
  if (data.structured_data) {
    resumeData = data.structured_data;
  } else if (data.executor) {
    // Try to extract JSON from executor output
    try {
      const jsonMatch = data.executor.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        resumeData = JSON.parse(jsonMatch[0]);
      }
    } catch (e) {
      console.warn('Failed to parse resume data from executor');
    }
  }
  
  const {
    name = 'Your Name',
    email,
    phone,
    linkedin,
    github,
    summary,
    education,
    experience = [],
    projects = [],
    skills = []
  } = resumeData;
  
  return (
    <div 
      data-testid="resume-preview"
      className="h-full bg-white rounded-xl overflow-hidden shadow-2xl"
    >
      <ScrollArea className="h-full">
        <div className="p-8 space-y-6 text-slate-800">
          {/* Header */}
          <div className="text-center border-b border-slate-200 pb-6">
            <h1 className="text-3xl font-bold text-slate-900">{name}</h1>
            
            <div className="flex flex-wrap items-center justify-center gap-4 mt-3 text-sm text-slate-600">
              {email && (
                <span className="flex items-center gap-1.5">
                  <Mail className="w-4 h-4" />
                  {email}
                </span>
              )}
              {phone && (
                <span className="flex items-center gap-1.5">
                  <Phone className="w-4 h-4" />
                  {phone}
                </span>
              )}
              {linkedin && (
                <span className="flex items-center gap-1.5">
                  <Linkedin className="w-4 h-4" />
                  {linkedin}
                </span>
              )}
              {github && (
                <span className="flex items-center gap-1.5">
                  <Github className="w-4 h-4" />
                  {github}
                </span>
              )}
            </div>
          </div>
          
          {/* Summary */}
          {summary && (
            <section>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-2">
                <User className="w-5 h-5 text-violet-600" />
                Professional Summary
              </h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                {parseMarkdownBold(summary)}
              </p>
            </section>
          )}
          
          {/* Experience */}
          {experience.length > 0 && (
            <section>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-4">
                <Briefcase className="w-5 h-5 text-violet-600" />
                Professional Experience
              </h2>
              <div className="space-y-5">
                {experience.map((exp, idx) => (
                  <div key={idx} className="border-l-2 border-violet-200 pl-4">
                    <h3 className="font-semibold text-slate-900">
                      {exp.role || exp.title}
                    </h3>
                    <p className="text-violet-600 text-sm font-medium">
                      {exp.company}
                    </p>
                    {formatDescription(exp.description || exp.details)}
                  </div>
                ))}
              </div>
            </section>
          )}
          
          {/* Projects */}
          {projects.length > 0 && (
            <section>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-4">
                <FolderOpen className="w-5 h-5 text-violet-600" />
                Projects
              </h2>
              <div className="space-y-5">
                {projects.map((proj, idx) => (
                  <div key={idx} className="border-l-2 border-violet-200 pl-4">
                    <h3 className="font-semibold text-slate-900">{proj.title}</h3>
                    {formatDescription(proj.details)}
                  </div>
                ))}
              </div>
            </section>
          )}
          
          {/* Skills */}
          {skills.length > 0 && (
            <section>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-3">
                <Wrench className="w-5 h-5 text-violet-600" />
                Technical Skills
              </h2>
              <div className="space-y-2">
                {skills.map((skill, idx) => (
                  <p key={idx} className="text-sm text-slate-600">
                    {parseMarkdownBold(skill)}
                  </p>
                ))}
              </div>
            </section>
          )}
          
          {/* Education */}
          {education && (
            <section>
              <h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900 mb-2">
                <GraduationCap className="w-5 h-5 text-violet-600" />
                Education
              </h2>
              <p className="text-slate-600 text-sm whitespace-pre-line">
                {education.replace(/\\n/g, '\n')}
              </p>
            </section>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

export default ResumePreview;
