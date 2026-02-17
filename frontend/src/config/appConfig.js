/**
 * App Configuration
 * Editable marketing text and theme configuration
 */

export const APP_CONFIG = {
  // Branding
  brand: {
    name: "ResumeAI",
    tagline: "Transform your resume with AI precision",
    description: "Watch our AI agents analyze, optimize, and transform your resume in real-time for maximum ATS compatibility."
  },
  
  // Landing page text
  landing: {
    headline: "AI-Powered Resume Optimization",
    subheadline: "Let our multi-agent AI system analyze your resume against job descriptions and optimize it for ATS systems.",
    uploadLabel: "Upload Your Resume",
    uploadHint: "PDF format only",
    jobDescLabel: "Paste Job Description",
    jobDescPlaceholder: "Paste the complete job description here...",
    submitButton: "Optimize Resume",
    processingButton: "Processing..."
  },
  
  // Agent descriptions
  agents: {
    planner: {
      name: "Planner Agent",
      description: "Analyzes resume gaps and creates optimization strategy",
      icon: "brain"
    },
    executor: {
      name: "Executor Agent", 
      description: "Rewrites and formats resume with ATS keywords",
      icon: "cog"
    },
    critic: {
      name: "Critic Agent",
      description: "Validates data preservation and template compliance",
      icon: "shield-check"
    }
  },
  
  // Templates
  templates: [
    { value: "harvard", label: "Harvard Business Style" }
  ],
  
  // Results text
  results: {
    scoreLabel: "ATS Score",
    downloadButton: "Download Optimized Resume",
    criticalIssuesLabel: "Critical Issues",
    suggestionsLabel: "Suggested Improvements",
    skillsGroupNote: "Skills grouped for readability — no skills were removed."
  },
  
  // Theme colors (CSS variables)
  theme: {
    primary: "#8b5cf6",      // Purple
    secondary: "#06b6d4",    // Cyan
    accent: "#f59e0b",       // Amber
    background: "#0f0f1a",   // Dark navy
    surface: "#1a1a2e",      // Slightly lighter
    text: "#e2e8f0",         // Light gray
    muted: "#64748b"         // Slate
  }
};

export default APP_CONFIG;
