# Multi-Agent AI Resume Optimizer

> 3-agent pipeline that rewrites resumes for ATS compatibility — 
> with adversarial critique, LLM-as-Judge evaluation, and 
> measurable before/after scoring.

[![Live Demo](https://img.shields.io/badge/Demo-Live%20on%20Vercel-brightgreen)](https://multi-agentic-ai-system-jwj3.vercel.app/)
[![API](https://img.shields.io/badge/API-Live%20on%20Render-blue)](https://ai-resume-optimizer-api.onrender.com)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-orange.svg)](https://crewai.com)

---

## The Problem

**75% of resumes never reach a human recruiter.**

ATS systems automatically reject candidates — not because 
they're underqualified, but because of keyword mismatch, 
poor formatting, and weak section structure.

Manual resume tailoring per job application takes 45-60 
minutes. Most candidates don't do it. This system does it 
in under 2 minutes.

---

## What This System Does

A production-style multi-agent pipeline where 3 specialized 
AI agents collaborate to analyze, rewrite, and validate 
your resume against any job description:
```
Resume + Job Description
         │
         ▼
┌─────────────────┐
│  Planner Agent  │  Analyzes JD, identifies keyword gaps,
│                 │  maps required skills to resume sections
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Executor Agent  │  Rewrites resume sections strategically,
│                 │  integrates keywords naturally
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Critic Agent   │  Adversarially validates output —
│  (Adversarial)  │  checks for keyword stuffing, lost
│                 │  context, authenticity issues
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM-as-Judge    │  Scores result across 4 dimensions
│ Eval Layer      │  with weighted overall score
└────────┬────────┘
         │
         ▼
   Optimized Resume
   + Score Report
```

---

## Results

| Metric | Score |
|--------|-------|
| Average ATS keyword match improvement | ~40% |
| Processing time per resume | < 2 minutes |
| LLM Judge dimensions scored | 4 |
| Agent pipeline stages | 3 + eval layer |

**LLM-as-Judge scores each output on:**
- Keyword Match Rate (0–100)
- Readability & Clarity (0–100)
- Authenticity Score (0–100)
- ATS Formatting Compliance (0–100)
- **Weighted Overall Score**

---

## Key Features

**Multi-Agent Orchestration (CrewAI)**  
Sequential agent flow with task delegation and 
memory handling — each agent has a distinct role 
and cannot override another's domain.

**Adversarial Critic Agent**  
The critic is prompted to find flaws, not confirm 
success. It checks: Did we lose original experience? 
Are keywords naturally integrated? Does this still 
sound human? If it fails, the pipeline retries.

**LLM-as-Judge Evaluation Layer**  
A separate judge LLM scores the final output 
independently — not the same model that generated 
it. Scores are logged to JSON for tracking 
improvement across runs.

**Self-RAG with Hybrid Retrieval**  
Integrated LlamaIndex Self-RAG with hybrid retrieval 
pipeline and reranking. Critic-guided retrieval loop 
reduces hallucinations in rewritten content.

**Feedback Loop & Score History**  
Thread-safe score history stored across sessions. 
Verdict-based retry and rollback logic — if judge 
score drops below threshold, system rolls back to 
previous version.

**Before/After Comparison UI**  
Side-by-side view of original vs optimized resume 
with score delta shown per section.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Orchestration | CrewAI | Multi-agent pipeline management |
| LLM Interface | LangChain + LlamaIndex | LLM calls, RAG, retrieval |
| Backend API | FastAPI | Agent workflow exposure via REST |
| Eval Layer | LLM-as-Judge (custom) | Output quality scoring |
| Memory | JSON + thread-safe store | Score history, feedback loop |
| Frontend | React (Next.js) | UI, before/after comparison |
| Deployment | Vercel + Render | Frontend + API hosting |

---

## Live Demo

**Frontend:** https://multi-agentic-ai-system-jwj3.vercel.app/  
**API Docs:** https://ai-resume-optimizer-api.onrender.com/docs

**Try it:**
1. Paste your resume text
2. Paste any job description
3. Watch the 3-agent pipeline run in real time
4. See before/after scores from the LLM Judge

---

## Architecture
```
frontend/          # React UI — input form, agent progress, 
│                  # before/after comparison, judge scores
│
agents/
│  planner.py      # Analyzes JD, produces keyword gap report
│  executor.py     # Rewrites resume using planner output
│  critic.py       # Adversarial validation, retry trigger
│
api/
│  main.py         # FastAPI — /optimize, /score, /history
│  crew.py         # CrewAI orchestration, retry/rollback logic
│
rag/               # Self-RAG pipeline, hybrid retrieval
memory/            # Score history, feedback loop storage
training/          # DPO fine-tuning pipeline (preference alignment)
```

---

## How to Run Locally
```bash
# 1. Clone the repo
git clone https://github.com/Midhun-12345678/Multi-Agentic-AI-System.git
cd Multi-Agentic-AI-System

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env
# Add your LLM API key to .env

# 4. Start backend
uvicorn main:app --reload --port 8000

# 5. Start frontend
cd frontend && npm install && npm run dev

# 6. Open http://localhost:3000
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/optimize` | POST | Run full 3-agent pipeline on resume + JD |
| `/score` | GET | Get LLM Judge scores for last run |
| `/history` | GET | Score history across all runs |
| `/health` | GET | API health check |

---

## Design Decisions

**Why CrewAI over a single LLM call?**  
A single prompt cannot reliably plan, execute, AND 
critique simultaneously. Separating concerns into 
specialized agents with distinct system prompts 
produces measurably better output — and makes 
failure points debuggable.

**Why an adversarial critic instead of a validating one?**  
A critic prompted to "confirm quality" agrees too 
easily. An adversarial critic prompted to "find 
everything wrong" catches keyword stuffing, lost 
context, and authenticity issues that a standard 
validator misses.

**Why LLM-as-Judge instead of rule-based scoring?**  
ATS systems vary across vendors. Rule-based keyword 
counting misses semantic matches. An LLM judge 
evaluates natural language quality the same way a 
human recruiter would — while still producing 
structured numeric scores.

---

## Future Improvements

- Fine-tuned critic model on human preference data (DPO)
- A/B testing framework to compare pipeline versions
- Support for PDF upload and formatted PDF output
- Per-industry keyword databases for domain-specific optimization
- Real ATS simulation using vendor-specific scoring models

---

## Author

**Midhun M** — AI/ML Engineer  
[GitHub](https://github.com/Midhun-12345678) · 
[LinkedIn](https://linkedin.com/in/midhun-m-d2001) · 
[Portfolio](https://my-portfolio-lilac-gamma.vercel.app/)
