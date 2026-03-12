# AI Resume Optimizer - Knowledge Transfer Document

> **Complete System Documentation for Developers & AI Assistants**  
> Last Updated: March 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack & Dependencies](#2-tech-stack--dependencies)
3. [Architecture Overview](#3-architecture-overview)
4. [Agent System (CrewAI)](#4-agent-system-crewai)
5. [RAG System](#5-rag-system)
6. [Backend API (FastAPI)](#6-backend-api-fastapi)
7. [Frontend (React)](#7-frontend-react)
8. [Templates & PDF Generation](#8-templates--pdf-generation)
9. [Configuration](#9-configuration)
10. [Data Flow & State Management](#10-data-flow--state-management)
11. [Validation & ATS Scoring](#11-validation--ats-scoring)
12. [Known Issues & Limitations](#12-known-issues--limitations)
13. [Future Roadmap](#13-future-roadmap)
14. [Development Setup](#14-development-setup)
15. [Testing](#15-testing)

---

## 1. Project Overview

### What It Does

The **AI Resume Optimizer** is a production-grade multi-agent system that:
1. Takes a user's resume (PDF) and a target job description
2. Runs three collaborating AI agents (Planner → Executor → Critic)
3. Produces an ATS-optimized resume that preserves all original data
4. Generates a downloadable PDF in one of three professional templates

### Key Goals

- **ATS Optimization**: Incorporate relevant keywords naturally without fabrication
- **Data Integrity**: Zero data loss - all jobs, projects, skills preserved
- **Field Mapping**: 1:1 mapping from original resume to optimized output
- **Real-time Feedback**: WebSocket/polling-based progress updates
- **Template Flexibility**: Harvard, Professional, Classic layouts

### Project Structure

```
ai-goal-based-agentic-ai/
├── main.py                 # FastAPI entry point, job processing
├── crew.py                 # CrewAI orchestration, retry logic
├── ui.py                   # Streamlit demo UI (legacy)
├── pdf_generator.py        # PDF generation (pdfkit-based)
├── agents/                 # Agent definitions
│   ├── __init__.py         # LLM config, agent exports
│   ├── planner.py          # ATS Resume Strategist
│   ├── executor.py         # Resume Optimization Executor
│   └── critic.py           # Validation & Quality Reviewer
├── api/
│   └── rag_service.py      # RAG service (empty - future integration)
├── backend/
│   └── server.py           # Alternative backend with WebSocket
├── config/
│   ├── llm.py              # LLM settings (model, temperature, tokens)
│   ├── paths.py            # Directory paths
│   ├── templates.py        # Available templates list
│   └── template_contexts.py # Template-specific prompts & JSON structures
├── data/
│   ├── docs/               # RAG documents (empty)
│   └── jobs/               # Job persistence (JSON files)
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js          # Main app, screen flow
│   │   ├── components/     # UI components
│   │   ├── hooks/          # useJobPolling, use-toast
│   │   ├── services/       # API client
│   │   └── config/         # appConfig.js
│   └── package.json
├── memory/
│   └── PRD.md              # Product Requirements Document
├── rag/                    # RAG modules (available but not integrated)
│   ├── indexer.py          # Document indexing
│   ├── loader.py           # Document loading
│   ├── retriever.py        # Vector retrieval
│   ├── reranker.py         # Cross-encoder reranking
│   └── self_rag.py         # Iterative retrieval loop
├── schemas/
│   └── resume_schema.py    # Pydantic data models
├── services/
│   ├── pdf_service.py      # HTML to PDF (WeasyPrint)
│   └── template_renderer.py # Jinja2 rendering
├── templates/              # HTML templates (Jinja2)
│   ├── harvard.html
│   ├── professional.html
│   └── classic.html
├── training/               # DPO fine-tuning (future)
│   ├── train_dpo.py
│   └── data/preferences.json
├── utils/                  # Utility modules
│   ├── ats_scorer.py       # Keyword extraction & scoring
│   ├── field_mapper.py     # Baseline extraction
│   ├── formatter.py        # Text to JSON fallback
│   ├── job_store.py        # File-based persistence
│   ├── job_tracker.py      # In-memory tracking
│   ├── pdf_generator.py    # ReportLab-based PDF
│   ├── pre_pdf_validator.py # Data integrity validation
│   ├── resume_reader.py    # PDF text extraction
│   ├── resume_structurer.py # Markdown to schema parser
│   └── validation_parser.py # Critic output parsing
├── requirements.txt        # Python dependencies
└── test_reports/           # Test results
```

---

## 2. Tech Stack & Dependencies

### Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | FastAPI | Latest | REST API & WebSocket |
| **Async Server** | Uvicorn | Latest | ASGI server |
| **Agent Framework** | CrewAI | Latest | Multi-agent orchestration |
| **LLM Client** | OpenAI | ~1.83.0 | GPT-4o-mini integration |
| **PDF Extraction** | pdfplumber/PyPDF2 | Latest | Resume text extraction |
| **PDF Generation** | WeasyPrint | Latest | HTML → PDF conversion |
| **Templating** | Jinja2 | Latest | HTML rendering |
| **RAG** | LlamaIndex | Latest | Vector indexing (available) |
| **Reranking** | sentence-transformers | Latest | Cross-encoder (available) |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Framework** | React | 18.2.0 | UI library |
| **Styling** | TailwindCSS | 3.4.17 | Utility-first CSS |
| **Components** | Radix UI | Latest | Accessible primitives |
| **HTTP Client** | Axios | 1.8.4 | API communication |
| **Forms** | React Hook Form | 7.56.2 | Form management |
| **Validation** | Zod | 3.24.4 | Schema validation |
| **Charts** | Recharts | 3.6.0 | ATS score visualization |

### Python Dependencies (`requirements.txt`)

```
crewai
fastapi
python-dotenv
uvicorn[standard]
openai~=1.83.0
tokenizers~=0.20.3
PyPDF2
jinja2
weasyprint
streamlit
requests
python-multipart
```

### Additional for RAG (install separately)

```bash
pip install llama-index sentence-transformers
```

---

## 3. Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────────┐ │
│  │   Upload Panel  │ →  │ Agent Timeline   │ →  │   Results & Download    │ │
│  │  (Resume + JD)  │    │ (Live Progress)  │    │ (Comparison + PDF)      │ │
│  └─────────────────┘    └──────────────────┘    └─────────────────────────┘ │
│                              React + TailwindCSS                             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP/WebSocket
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            BACKEND API (FastAPI)                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  POST /api/optimize-resume   →  Creates job, returns job_id            ││
│  │  GET /api/status/{job_id}    →  Returns agents status, progress        ││
│  │  WS /api/ws/{job_id}         →  Real-time event push (alternative)     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│  ┌─────────────────────────────────▼────────────────────────────────────┐   │
│  │                    BACKGROUND JOB PROCESSOR                          │   │
│  │  ThreadPoolExecutor (4 workers)                                      │   │
│  │  process_resume_job() → runs crew.py orchestration                   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENT ORCHESTRATION (CrewAI)                          │
│                                                                              │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐              │
│   │   PLANNER    │  →   │   EXECUTOR   │  →   │    CRITIC    │              │
│   │              │      │              │      │              │              │
│   │ • Analyze JD │      │ • Rewrite    │      │ • Validate   │              │
│   │ • ATS gaps   │      │ • Output JSON│      │ • Field map  │              │
│   │ • Strategy   │      │ • Preserve   │      │ • Data loss  │              │
│   └──────────────┘      └──────────────┘      └──────────────┘              │
│           │                    │                     │                       │
│           │                    │                     ▼                       │
│           │                    │              ┌─────────────┐                │
│           │                    │              │ RETRY LOOP  │                │
│           │                    │◄─────────────│ (max 2x)    │                │
│           │ (cached)           │              └─────────────┘                │
│           │                    │                                             │
│           └────────────────────┴────────────────────────────────────────────│
│                                                                              │
│   Using: GPT-4o-mini (temp: 0.3, max_tokens: 8192)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POST-PROCESSING PIPELINE                             │
│                                                                              │
│   ┌─────────────┐   ┌─────────────────┐   ┌─────────────┐   ┌────────────┐  │
│   │ JSON Parse  │ → │ Pre-PDF         │ → │ Jinja2      │ → │ WeasyPrint │  │
│   │ (or fallback│   │ Validation      │   │ Render HTML │   │ → PDF      │  │
│   │  to markdown)   │ (data integrity)│   │             │   │ → Base64   │  │
│   └─────────────┘   └─────────────────┘   └─────────────┘   └────────────┘  │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │ ATS SCORING: Compare original vs optimized keyword match %          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FILE PERSISTENCE                                   │
│                                                                              │
│   data/jobs/{job_id}.json                                                   │
│   ├── status: queued | processing | complete | error                        │
│   ├── progress: 0-100                                                       │
│   ├── agents: { planner: {...}, executor: {...}, critic: {...} }            │
│   ├── result: { pdf_base64, ats_score, validation, ... }                    │
│   └── timestamps: created_at, updated_at                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Connections

| From | To | Method | Purpose |
|------|-----|--------|---------|
| Frontend | Backend | HTTP POST | Submit job |
| Frontend | Backend | HTTP GET (polling) | Check status |
| Frontend | Backend | WebSocket | Real-time updates (optional) |
| Backend | CrewAI | Python function | Run agents |
| Agents | OpenAI | HTTP API | LLM inference |
| Backend | WeasyPrint | Python library | Generate PDF |
| Backend | FileSystem | JSON files | Persist jobs |

---

## 4. Agent System (CrewAI)

### Agent Pipeline

The system uses three specialized agents that execute **sequentially**:

```
Original Resume + Job Description
              │
              ▼
    ┌─────────────────┐
    │  PLANNER AGENT  │  "ATS Resume Strategist"
    │                 │
    │  Inputs:        │
    │  • Resume text  │
    │  • Job description
    │  • ATS keywords │
    │  • Template type│
    │  • Page count   │
    │                 │
    │  Output:        │
    │  • Strategy plan│
    │  • Gap analysis │
    │  • Keyword recs │
    └────────┬────────┘
             │ (strategy passed as context)
             ▼
    ┌─────────────────┐
    │ EXECUTOR AGENT  │  "Resume Optimization Executor"
    │                 │
    │  Inputs:        │
    │  • Original resume (SOURCE OF TRUTH)
    │  • Planner strategy
    │  • Template JSON structure
    │  • Corrective prompts (on retry)
    │                 │
    │  Output:        │
    │  • Valid JSON   │
    │  • All fields   │
    │  • Optimized text
    └────────┬────────┘
             │ (JSON output for validation)
             ▼
    ┌─────────────────┐
    │  CRITIC AGENT   │  "Hiring Quality Reviewer"
    │                 │
    │  Inputs:        │
    │  • Original resume
    │  • Executor JSON│
    │  • Planner context
    │                 │
    │  Output:        │
    │  • Validation report
    │  • Field mapping│
    │  • Data integrity
    │  • Corrections  │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  VALID OUTPUT?  │
    │                 │
    │  Yes → Continue │
    │  No  → Retry    │
    │  (max 2 retries)│
    └─────────────────┘
```

### Agent Definitions

#### 1. Planner Agent (`agents/planner.py`)

```python
Agent(
    role="ATS Resume Strategist",
    goal="Analyze resume and job description to create ATS optimization plan",
    backstory="Expert in ATS systems, recruiter screening, and keyword alignment",
    llm=llm,  # gpt-4o-mini
    verbose=True,
    allow_delegation=False
)
```

**Task Description** (from `crew.py`):
- Analyze resume structure against target job description
- Identify content gaps and missing keywords
- Recommend natural keyword incorporation (no fabrication)
- Consider template-specific styling
- Provide strategy for page constraints

**Output**: Structured improvement plan with template-specific recommendations

#### 2. Executor Agent (`agents/executor.py`)

```python
Agent(
    role="Resume Optimization Executor",
    goal="Rewrite resume using ATS strategy while preserving truth and identity",
    backstory="Professional resume writer with hiring domain experience",
    llm=llm,
    verbose=True,
    allow_delegation=False
)
```

**Task Description**:
- Extract ALL data from original resume (critical source of truth)
- Output valid JSON matching template structure
- Preserve ALL bullet points, skills, certifications, dates, company names
- Optimize wording with action verbs and keyword incorporation
- Maintain 1:1 field mapping

**Critical Preservation Rules**:
- ❌ Cannot drop bullet points
- ❌ Cannot remove skills not in job description
- ❌ Cannot delete certifications, awards, education
- ❌ Cannot shorten company names or remove dates
- ✅ Can reword with better action verbs
- ✅ Can group skills by category
- ✅ Can enhance bullets with job keywords naturally

**Output**: Valid JSON object with complete resume structure

#### 3. Critic Agent (`agents/critic.py`)

```python
Agent(
    role="Hiring Quality Reviewer, Resume Formatter & Field Mapping Validator",
    goal="Validate 100% field mapping accuracy and strict markdown/JSON format",
    backstory="Senior hiring manager with real interview experience",
    llm=llm,
    verbose=True,
    allow_delegation=False
)
```

**Validation Checks**:
1. JSON structure validity
2. Job mapping: X original → X in JSON
3. Project mapping: X original → X in JSON
4. Contact info preservation (name, email, phone, LinkedIn, GitHub)
5. Data integrity assessment (COMPLETE/INCOMPLETE)
6. Template compliance

**Output**: Comprehensive validation report with pass/fail and corrective feedback

### Retry Logic (`crew.py`)

```python
MAX_RETRIES = 2

# Retry triggers:
# - JSON parsing failures
# - Critical validation failures (jobs missing, projects missing)
# - Data integrity score < threshold

# Optimization:
# - Planner output is CACHED and reused across retries
# - Only Executor and Critic are re-run on retry
# - Saves ~1 LLM call per retry cycle

# Corrective prompts appended to Executor on retry:
# "CRITICAL: Previous attempt failed validation. Issues found: {critic_feedback}"
```

### Agent Callbacks

Real-time progress updates via callbacks:

```python
def on_task_complete(task_output):
    # Called when each agent completes
    job_store.update_agent_status(job_id, agent_name, "complete", output)

def on_step(step_output):
    # Called during agent execution (throttled every 3 seconds)
    job_store.add_agent_message(job_id, agent_name, message)
```

### LLM Configuration (`agents/__init__.py`)

```python
llm = LLM(
    model="gpt-4o-mini",  # or env OPENAI_MODEL
    api_key=api_key,      # from env OPENAI_API_KEY
    temperature=0.3       # Low for consistency
)
```

---

## 5. RAG System

> ⚠️ **Status**: The RAG system is **implemented but NOT integrated** into the main workflow. All modules are available and can be activated for future enhancements.

### Components

```
rag/
├── loader.py      # Document loading (SimpleDirectoryReader)
├── indexer.py     # Vector index creation (VectorStoreIndex)
├── retriever.py   # Vector retrieval (top-k=5)
├── reranker.py    # Cross-encoder reranking (ms-marco-MiniLM)
└── self_rag.py    # Iterative retrieval loop (max 2 rounds)
```

### Document Loading (`rag/loader.py`)

```python
from llama_index.core import SimpleDirectoryReader

def load_documents(directory="data/docs/"):
    """Load documents from filesystem"""
    # Supports: PDF, TXT, DOCX, MD, HTML
    # Recursive loading from subdirectories
    # Excludes hidden files
    return SimpleDirectoryReader(directory, recursive=True).load_data()
```

### Document Indexing (`rag/indexer.py`)

```python
from llama_index.core import VectorStoreIndex

def build_index(documents):
    """Create vector index from documents"""
    # Uses default embedding model (OpenAI or local)
    # In-memory vector store (can swap for Pinecone, Chroma)
    return VectorStoreIndex.from_documents(documents)
```

### Retrieval (`rag/retriever.py`)

```python
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine

def build_retriever(index):
    """Build retriever with top-k=5"""
    retriever = VectorIndexRetriever(index=index, similarity_top_k=5)
    return RetrieverQueryEngine.from_args(retriever=retriever)
```

### Reranking (`rag/reranker.py`)

```python
from sentence_transformers import CrossEncoder

model = CrossEncoder("sentence-transformers/cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, documents):
    """Rerank documents using cross-encoder"""
    # Pairs query with each doc, scores relevance
    # Returns sorted by score (descending)
    pairs = [(query, doc.text) for doc in documents]
    scores = model.predict(pairs)
    return sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
```

### Self-RAG Loop (`rag/self_rag.py`)

```python
def self_rag_loop(query, retriever, critic_agent=None, max_rounds=2):
    """Iterative retrieval with validation"""
    context = ""
    for round in range(max_rounds):
        # 1. Retrieve documents
        results = retriever.query(query)
        context += results.response
        
        # 2. Validate sufficiency (heuristic or critic)
        if len(context) > 300:  # Simple heuristic
            break
        # Or use critic_agent for AI-based validation
    
    return context
```

### How to Activate RAG

1. Add documents to `data/docs/`
2. Install dependencies: `pip install llama-index sentence-transformers`
3. In `crew.py`, import and use RAG for context:

```python
from rag.loader import load_documents
from rag.indexer import build_index
from rag.retriever import build_retriever
from rag.self_rag import self_rag_loop

# Build index once at startup
documents = load_documents()
index = build_index(documents)
retriever = build_retriever(index)

# Use in agent tasks
context = self_rag_loop(job_description, retriever, critic)
# Pass context to planner/executor prompts
```

---

## 6. Backend API (FastAPI)

### Entry Point (`main.py`)

```python
app = FastAPI(title="AI Resume Optimizer")
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)

# Startup: Load existing jobs, cleanup old jobs (>48h)
# Shutdown: Clean up thread pool

executor = ThreadPoolExecutor(max_workers=4)
```

### API Endpoints

#### POST `/api/optimize-resume`

Submit a resume optimization job.

**Request** (multipart/form-data):
```
resume: PDF file (required)
job_description: string (required, min 50 chars)
template: "professional" | "harvard" | "classic" (default: "harvard")
```

**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "queued",
  "message": "Job submitted successfully"
}
```

**Flow**:
1. Validate PDF file
2. Extract text from PDF (pdfplumber)
3. Extract ATS keywords from job description
4. Create job in file store
5. Submit to thread pool for background processing
6. Return job_id immediately

#### GET `/api/status/{job_id}`

Poll for job status updates.

**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "processing",  // queued | processing | complete | error
  "progress": 65,          // 0-100
  "agents": {
    "planner": {
      "status": "complete",
      "messages": [...],
      "started_at": "ISO timestamp",
      "completed_at": "ISO timestamp",
      "output": "strategy text..."
    },
    "executor": {
      "status": "running",
      "messages": [...],
      "started_at": "ISO timestamp"
    },
    "critic": {
      "status": "pending"
    }
  },
  "result": null,  // Populated when complete
  "error": null,
  "retry_count": 0
}
```

**When Complete**:
```json
{
  "status": "complete",
  "result": {
    "pdf_base64": "base64-encoded-pdf...",
    "ats_analysis": {
      "original_score": 45,
      "optimized_score": 82,
      "improvement": 37,
      "keywords_added": ["Python", "AWS", "Docker"],
      "keywords_matched": [...],
      "keywords_unmatched": [...]
    },
    "validation": {
      "data_integrity_score": 93,
      "experience_count": 4,
      "project_count": 3,
      "warnings": []
    }
  }
}
```

#### GET `/api/jobs`

List all jobs.

**Query Parameters**:
- `status`: Filter by status (optional)
- `limit`: Max results (optional)

#### DELETE `/api/jobs/{job_id}`

Delete a job and its data.

#### POST `/api/cleanup`

Manually cleanup old jobs (>48h).

#### GET `/api/`

Health check endpoint.

### WebSocket Endpoint (`backend/server.py`)

Alternative real-time updates via WebSocket:

```
WS /api/ws/{job_id}
```

**Events**:
- `connected` - Client connected
- `agent_started` - Agent begins processing
- `agent_message` - Progress message
- `agent_completed` - Agent finished with output
- `validation_warning` - Quality issue detected
- `job_completed` - Final result ready
- `job_failed` - Error occurred

### Background Processing

```python
def process_resume_job(job_id, resume_text, job_description, template, page_count, ats_keywords):
    """Background job processor"""
    try:
        # 1. Update status to processing
        job_store.update_job_status(job_id, "processing")
        
        # 2. Run agent crew
        result = run_crew(
            resume_text=resume_text,
            job_description=job_description,
            template=template,
            page_count=page_count,
            ats_keywords=ats_keywords,
            callbacks=make_callbacks(job_id)
        )
        
        # 3. Parse structured data
        if "structured_data" in result:
            resume_data = ResumeSchema.from_json(result["structured_data"])
        else:
            resume_data = structure_resume(result["executor"])
        
        # 4. Validate data integrity
        validation = validate_pre_pdf(resume_data, resume_text)
        
        # 5. Render HTML
        html = render_html(resume_data, template)
        
        # 6. Generate PDF
        pdf_base64 = html_to_pdf_base64(html)
        
        # 7. ATS scoring
        ats_analysis = analyze_ats_improvement(
            original=resume_text,
            optimized=str(resume_data),
            keywords=ats_keywords
        )
        
        # 8. Store result
        job_store.complete_job(job_id, {
            "pdf_base64": pdf_base64,
            "ats_analysis": ats_analysis,
            "validation": validation
        })
        
    except Exception as e:
        job_store.error_job(job_id, str(e))
```

---

## 7. Frontend (React)

### Screen Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  LANDING SCREEN                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     UploadPanel                           │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │  📎 Drag & drop resume PDF here                    │ │  │
│  │  │     or click to browse                             │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  📝 Job Description:                                     │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │ Paste the job description here...                  │ │  │
│  │  │ (minimum 50 characters)                            │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  │                                                           │  │
│  │  📋 Template: [Harvard ▼]                                │  │
│  │                                                           │  │
│  │  [🚀 Optimize Resume]                                    │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (submit)
┌─────────────────────────────────────────────────────────────────┐
│  PROCESSING SCREEN                                               │
│  ┌────────────────────────┬─────────────────────────────────┐   │
│  │    AgentTimeline       │       LiveConsole               │   │
│  │                        │                                 │   │
│  │  ○ Planner             │  14:32:05 [planner] Analyzing.. │   │
│  │    ├ Running...        │  14:32:08 [planner] Found gaps  │   │
│  │    └ "Analyzing gaps"  │  14:32:12 [executor] Writing..  │   │
│  │                        │  14:32:15 [critic] Validating   │   │
│  │  ○ Executor            │                                 │   │
│  │    └ Pending           │  [Auto-scroll terminal]         │   │
│  │                        │                                 │   │
│  │  ○ Critic              │                                 │   │
│  │    └ Pending           │                                 │   │
│  │                        │                                 │   │
│  └────────────────────────┴─────────────────────────────────┘   │
│                                                                  │
│  Progress: ████████████░░░░░░░░ 65%                             │
│  [Cancel]                                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (complete)
┌─────────────────────────────────────────────────────────────────┐
│  RESULTS SCREEN                                                  │
│  ┌────────────────────┬─────────────────────────────────────┐   │
│  │   ResultSummary    │   [Comparison] [Preview]            │   │
│  │                    │                                     │   │
│  │   ATS Score: 82%   │   ┌─────────────────────────────┐   │   │
│  │   +37% improvement │   │  ResumeComparison           │   │   │
│  │                    │   │  or                         │   │   │
│  │   Experience: 4    │   │  ResumePreview              │   │   │
│  │   Projects: 3      │   │                             │   │   │
│  │                    │   │                             │   │   │
│  │   ⚠️ 1 warning     │   │                             │   │   │
│  │                    │   │                             │   │   │
│  │   [📥 Download]    │   └─────────────────────────────┘   │   │
│  └────────────────────┴─────────────────────────────────────┘   │
│                                                                  │
│  [Optimize Another Resume]                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### `App.js`
- Main application with screen state machine
- States: `LANDING` → `PROCESSING` → `RESULTS`
- Manages job submission and polling

#### `UploadPanel.jsx`
- Drag & drop file upload (PDF only)
- Job description textarea (min 50 chars)
- Template selector (Harvard/Professional/Classic)
- Form validation and submit handling

#### `AgentTimeline.jsx`
- Vertical timeline of 3 agents
- Status badges: Pending, Running (spinner), Complete, Error
- Shows latest 3 messages per agent
- Severity badges: CRITICAL (red), WARNING (amber), INFO (blue)

#### `LiveConsole.jsx`
- Terminal-style log display
- Auto-scrolls to bottom
- Message formatting by severity
- Agent color coding (planner=violet, executor=amber, critic=emerald)
- Keeps last 50 messages

#### `ResultSummary.jsx`
- Large ATS score display with color coding
- Improvement percentage badge
- Field mapping status (experience/project counts)
- Critical warnings section
- Collapsible validation notes
- PDF download button (base64 → blob → download)

#### `ResumeComparison.jsx`
- Side-by-side score comparison
- Technical skills match progress bar
- Soft skills match progress bar
- Keyword analysis (added, matched, unmatched)

#### `ResumePreview.jsx`
- Clean white resume rendering
- Conditional section rendering
- Markdown parsing (**bold** support)
- Scrollable container

### Custom Hooks

#### `useJobPolling.js`

Adaptive polling strategy:

```javascript
// Polling intervals
const FAST_INTERVAL = 500;     // Agent running
const DEFAULT_INTERVAL = 1000; // Queued/pending
const SLOW_INTERVAL = 2000;    // Complete/error

// State returned
{
  status,           // 'complete' | 'error' | null
  agents: {
    planner: { status, messages: [] },
    executor: { status, messages: [] },
    critic: { status, messages: [] }
  },
  progress: 0-100,
  result: { ...final data },
  error: null,
  consoleMessages: [...last 50 messages],
  isConnected: boolean,
  disconnect: function
}
```

### API Client (`services/api.js`)

```javascript
const API_BASE = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

export const submitResume = (resumeFile, jobDescription, template) => {
  const formData = new FormData();
  formData.append('resume', resumeFile);
  formData.append('job_description', jobDescription);
  formData.append('template', template);
  return axios.post(`${API_BASE}/api/optimize-resume`, formData);
};

export const getJobStatus = (jobId) => {
  return axios.get(`${API_BASE}/api/status/${jobId}`);
};
```

### Configuration (`config/appConfig.js`)

```javascript
export const APP_CONFIG = {
  brand: {
    name: "ResumeAI",
    tagline: "Optimize your resume with AI"
  },
  agents: [
    { id: "planner", name: "Planner", description: "Analyzes and strategizes" },
    { id: "executor", name: "Executor", description: "Optimizes content" },
    { id: "critic", name: "Critic", description: "Validates quality" }
  ],
  templates: [
    { id: "harvard", name: "Harvard" },
    { id: "professional", name: "Professional" },
    { id: "classic", name: "Classic" }
  ],
  theme: {
    primary: "purple",
    secondary: "cyan"
  }
};
```

---

## 8. Templates & PDF Generation

### Available Templates

| Template | Style | Font | Border |
|----------|-------|------|--------|
| **Harvard** | Academic, serif | Crimson Text / Times | Dark red accent |
| **Professional** | Modern, sans-serif | Helvetica / Arial | None |
| **Classic** | Traditional, clean | Arial | None |

### Template Variables (Jinja2)

All templates use these variables:

```python
{
    "name": str,           # Required
    "email": str,          # Optional
    "phone": str,          # Optional
    "linkedin": str,       # Optional
    "github": str,         # Optional
    "summary": str,        # Professional summary (markdown supported)
    "skills": List[str],   # Skill items
    "experience": List[{
        "role": str,
        "company": str,
        "start_date": str,
        "end_date": str,
        "location": str,
        "description": str  # Bullet points separated by \n
    }],
    "projects": List[{
        "title": str,
        "tech_stack": str,
        "details": str      # Bullet points separated by \n
    }],
    "education": List[{
        "degree": str,
        "institution": str,
        "year": str,
        "details": str
    }],
    "certifications": List[str],
    "awards": List[str]
}
```

### Rendering Pipeline

```
Resume Data (Python objects)
        │
        ▼
template_renderer.py::render_html(resume_data, template_name)
        │
        │  1. Load template file (templates/{name}.html)
        │  2. Apply md2html filter (markdown → HTML)
        │  3. Render Jinja2 template with data
        │
        ▼
HTML String
        │
        ▼
pdf_service.py::html_to_pdf_base64(html_content)
        │
        │  1. Parse HTML with WeasyPrint
        │  2. Render to PDF bytes
        │  3. Encode as base64
        │
        ▼
Base64 PDF String (for API response)
```

### PDF Styling

All templates include `@page` CSS:

```css
@page {
    size: A4;          /* 210mm × 297mm */
    margin: 1cm;       /* Or 2cm for Harvard */
}

body {
    font-size: 10.5pt;
    line-height: 1.4;
}
```

### Template Context System (`config/template_contexts.py`)

Each template has specific context with:
- Structure guidelines (section order)
- Formatting rules (bullet length, emphasis)
- JSON structure example for Executor
- Example output snippets

```python
TEMPLATE_CONTEXTS = {
    "harvard": {
        "structure": "Center-aligned header, Summary → Education → Experience → Projects → Skills",
        "rules": [
            "One-line bullets (50-80 chars)",
            "Bold company/project names",
            "Formal, concise language"
        ],
        "json_structure_example": {...}
    },
    "professional": {...},
    "classic": {...}
}

def get_template_prompt_context(template_name):
    """Returns formatted prompt for LLM agents"""
    ...

def get_json_structure_prompt(template_name):
    """Returns JSON structure specification for Executor"""
    ...
```

---

## 9. Configuration

### LLM Settings (`config/llm.py`)

```python
# Model Settings
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Required

# Generation Settings
TEMPERATURE = 0.3       # Low for consistency
MAX_TOKENS = 8192       # Supports 2-page resumes
```

### Directory Paths (`config/paths.py`)

```python
BASE_DIR = Path(__file__).parent.parent  # Project root
TEMPLATES_DIR = BASE_DIR / "templates"   # HTML templates
OUTPUT_DIR = BASE_DIR / "output"         # Generated files
DOCS_DIR = BASE_DIR / "data" / "docs"    # RAG documents
JOBS_DIR = BASE_DIR / "data" / "jobs"    # Job persistence
```

### Template Configuration (`config/templates.py`)

```python
DEFAULT_TEMPLATE = "harvard"

AVAILABLE_TEMPLATES = {
    "professional": {"html": "professional.html", "css": "professional.css"},
    "harvard": {"html": "harvard.html", "css": "harvard.css"},
    "classic": {"html": "classic.html", "css": "classic.css"}
}
```

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-your-api-key-here

# Optional
OPENAI_MODEL=gpt-4o-mini    # Default: gpt-4o-mini
```

### Frontend Environment

```bash
# .env or environment
REACT_APP_BACKEND_URL=http://localhost:8001  # Default: localhost:8000
```

---

## 10. Data Flow & State Management

### Job Lifecycle

```
                    ┌──────────────────┐
                    │     QUEUED       │
                    │                  │
                    │ • Job created    │
                    │ • File saved     │
                    │ • Agents pending │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   PROCESSING     │
                    │                  │
                    │ • Planner runs   │
                    │ • Executor runs  │
                    │ • Critic runs    │
                    │ • Retries (0-2)  │
                    └────────┬─────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
    ┌──────────────────┐          ┌──────────────────┐
    │    COMPLETE      │          │     ERROR        │
    │                  │          │                  │
    │ • PDF generated  │          │ • Error message  │
    │ • ATS scored     │          │ • Stack trace    │
    │ • Result stored  │          │ • Partial output │
    └──────────────────┘          └──────────────────┘
```

### Job State Schema (`data/jobs/{job_id}.json`)

```json
{
  "job_id": "uuid-string",
  "status": "queued | processing | complete | error",
  "progress": 0-100,
  "created_at": "2026-03-12T10:30:00Z",
  "updated_at": "2026-03-12T10:35:00Z",
  "template": "harvard",
  "resume_text": "Full text of original resume...",
  "job_description": "Full job description text...",
  "agents": {
    "planner": {
      "status": "pending | running | complete | error",
      "messages": [
        {
          "timestamp": "2026-03-12T10:31:00Z",
          "type": "progress",
          "content": "Analyzing resume structure...",
          "severity": "info"
        }
      ],
      "started_at": null,
      "completed_at": null,
      "output": null
    },
    "executor": { ... },
    "critic": { ... }
  },
  "result": {
    "pdf_base64": "...",
    "ats_analysis": { ... },
    "validation": { ... },
    "structured_data": { ... }
  },
  "error": null,
  "validation_warnings": [],
  "retry_count": 0
}
```

### Progress Calculation

```python
# Progress based on agent status
PROGRESS_MAP = {
    "planner_pending": 0,
    "planner_running": 10,
    "planner_complete": 33,
    "executor_running": 50,
    "executor_complete": 66,
    "critic_running": 80,
    "critic_complete": 100
}
```

### File-Based Persistence (`utils/job_store.py`)

```python
class FileJobStore:
    """Manages job state across filesystem"""
    
    def __init__(self, jobs_dir="data/jobs"):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
    
    def create_job(self, resume_text, job_description, template):
        """Create new job with unique ID"""
        job_id = str(uuid.uuid4())
        job_data = {...}
        self._save_job(job_id, job_data)
        return job_id
    
    def _save_job(self, job_id, data):
        """Atomic write using temp file"""
        temp_path = self.jobs_dir / f"{job_id}.tmp"
        final_path = self.jobs_dir / f"{job_id}.json"
        with open(temp_path, "w") as f:
            json.dump(data, f)
        temp_path.replace(final_path)  # Atomic
```

### Startup Behavior

```python
@app.on_event("startup")
async def startup():
    # 1. Load existing jobs from disk
    jobs = job_store.load_all_jobs()
    
    # 2. Resume "processing" jobs that were interrupted
    for job in jobs:
        if job.status == "processing":
            job.status = "error"
            job.error = "Server restarted during processing"
    
    # 3. Cleanup jobs older than 48 hours
    job_store.cleanup_old_jobs(max_age_hours=48)
```

---

## 11. Validation & ATS Scoring

### Baseline Extraction (`utils/field_mapper.py`)

Before agents run, extract original resume data:

```python
@dataclass
class ResumeBaseline:
    name: str
    email: str
    phone: str
    linkedin: str
    github: str
    experience_count: int
    project_count: int
    skill_count: int
    companies: List[str]
    project_titles: List[str]
    skills: List[str]

def extract_baseline(resume_text: str) -> ResumeBaseline:
    """Extract source-of-truth data from original resume"""
    return ResumeBaseline(
        name=extract_name(resume_text),
        email=extract_email(resume_text),
        experience_count=count_experience_entries(resume_text),
        # ... etc
    )
```

### Pre-PDF Validation (`utils/pre_pdf_validator.py`)

Validate data integrity before rendering:

```python
def validate_pre_pdf(resume_data: ResumeSchema, original_text: str) -> dict:
    """Ensure no data loss in final output"""
    baseline = extract_baseline(original_text)
    
    checks = {
        "name_present": bool(resume_data.name),
        "email_preserved": baseline.email in resume_data.email,
        "experience_count": len(resume_data.experience) >= baseline.experience_count,
        "project_count": len(resume_data.projects) >= baseline.project_count,
        "skills_retained": len(resume_data.skills) >= baseline.skill_count * 0.8
    }
    
    # Calculate integrity score (0-100)
    score = calculate_weighted_score(checks)
    
    return {
        "data_integrity_score": score,
        "checks": checks,
        "warnings": generate_warnings(checks)
    }
```

### ATS Scoring (`utils/ats_scorer.py`)

```python
# Keyword categories
TECHNICAL_KEYWORDS = [
    "Python", "JavaScript", "TypeScript", "React", "Vue", "Angular",
    "Node.js", "Django", "Flask", "FastAPI", "AWS", "Azure", "GCP",
    "Docker", "Kubernetes", "CI/CD", "Git", "SQL", "MongoDB",
    "Machine Learning", "AI", "TensorFlow", "PyTorch", "REST API",
    "GraphQL", "Microservices", "Agile", "Scrum"
]

SOFT_SKILLS = [
    "communication", "leadership", "teamwork", "problem-solving",
    "collaboration", "mentoring", "presentation", "analytical"
]

def extract_keywords_from_job_description(job_description: str) -> dict:
    """Extract keywords from job description"""
    return {
        "technical_skills": [...],
        "soft_skills": [...],
        "frequent_keywords": [...],  # Appears 2+ times
        "weighted_keywords": {...}
    }

def score_resume_against_keywords(resume_text: str, keywords: dict) -> float:
    """Score resume match (0-100)"""
    matched = count_matched_keywords(resume_text, keywords)
    total = len(keywords["all"])
    return (matched / total) * 100

def analyze_ats_improvement(original: str, optimized: str, keywords: dict) -> dict:
    """Compare original vs optimized scores"""
    original_score = score_resume_against_keywords(original, keywords)
    optimized_score = score_resume_against_keywords(optimized, keywords)
    
    return {
        "original_score": original_score,
        "optimized_score": optimized_score,
        "improvement": optimized_score - original_score,
        "keywords_added": find_new_keywords(original, optimized, keywords),
        "keywords_matched": [...],
        "keywords_unmatched": [...]
    }
```

### Validation Parser (`utils/validation_parser.py`)

Parse Critic agent output:

```python
def parse_validation_report(critic_output: str) -> dict:
    """Parse critic's validation report"""
    return {
        "jobs_mapped": extract_count("Job mapping:", critic_output),
        "projects_mapped": extract_count("Project mapping:", critic_output),
        "contact_info": extract_status("Contact info:", critic_output),
        "data_integrity": extract_status("Data integrity:", critic_output),
        "format_compliance": extract_status("Format:", critic_output),
        "validation_passed": "PASS" in critic_output.upper(),
        "warnings": extract_warnings(critic_output)
    }
```

---

## 12. Known Issues & Limitations

### Critical Issues

| Issue | Impact | Status | Workaround |
|-------|--------|--------|------------|
| **OpenAI API Key** | Resume optimization fails | Ongoing | Provide valid API key in env |
| **RAG Not Integrated** | No document-based context | By Design | Available modules can be activated |

### Limitations

#### Agent System
- **Max 2 retries**: If validation fails 3 times, job errors out
- **Sequential only**: Agents cannot run in parallel
- **Single LLM**: All agents use same model (gpt-4o-mini)
- **No memory**: Agents don't remember previous jobs

#### Resume Parsing
- **PDF only**: No Word doc, Google Doc support
- **Text extraction**: Complex layouts may extract poorly
- **Tables/columns**: May not preserve structure correctly

#### Templates
- **Fixed 3 templates**: Cannot add custom templates via UI
- **No live preview**: Template preview only after generation
- **English only**: Templates assume English content

#### Frontend
- **No authentication**: Anyone can submit jobs
- **No job history**: Jobs lost after browser refresh (unless polling active)
- **Single file only**: Cannot batch process multiple resumes

### Edge Cases to Watch

1. **Empty sections**: Resume with no projects, no skills
2. **Non-standard headings**: "Work History" instead of "Experience"
3. **Multiple pages**: Page count > 2 may exceed token limits
4. **Special characters**: Unicode, emojis in resume
5. **Excessive bullets**: 20+ bullet points per job

### Error Handling

```python
# Common error scenarios and responses
try:
    result = run_crew(...)
except json.JSONDecodeError:
    # Executor didn't return valid JSON
    # Falls back to markdown parsing

except OpenAIError as e:
    # API issues (rate limit, auth, timeout)
    job.status = "error"
    job.error = str(e)

except ValidationError:
    # Critical data loss detected
    if retry_count < MAX_RETRIES:
        retry_with_corrections()
    else:
        job.status = "error"
```

---

## 13. Future Roadmap

### P1 (High Priority)

| Feature | Description | Effort |
|---------|-------------|--------|
| End-to-end testing | Test with various resume formats | Medium |
| WebSocket reconnection | Better handling of dropped connections | Low |
| Error recovery UX | User-friendly error messages | Low |
| RAG integration | Activate document retrieval for context | Medium |

### P2 (Medium Priority)

| Feature | Description | Effort |
|---------|-------------|--------|
| Template preview | Preview before generation | Medium |
| Job history | Persist across sessions | Medium |
| Export formats | DOCX, TXT in addition to PDF | Medium |
| Multiple templates | Generate all 3 at once | Low |

### P3 (Nice to Have)

| Feature | Description | Effort |
|---------|-------------|--------|
| User accounts | Authentication and history | High |
| Analytics dashboard | Usage metrics, success rates | High |
| Resume comparison | Compare multiple versions | Medium |
| Batch processing | Upload multiple resumes | High |

### DPO Fine-tuning (Prepared)

The `training/` folder contains a DPO (Direct Preference Optimization) pipeline:

```python
# training/train_dpo.py
# Model: Mistral-7B-Instruct-v0.2
# Method: LoRA (r=8, alpha=16)
# Data: training/data/preferences.json

# Requires separate venv with training dependencies:
# pip install trl transformers peft datasets
```

**Purpose**: Fine-tune agents for preference-aligned responses (better formatting, keyword incorporation, etc.)

---

## 14. Development Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd ai-goal-based-agentic-ai

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export OPENAI_API_KEY=sk-your-key-here
# Or create .env file with same

# 5. Start backend server
uvicorn main:app --reload --port 8001
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Set environment (optional)
export REACT_APP_BACKEND_URL=http://localhost:8001

# 4. Start development server
npm start
# Opens http://localhost:3000
```

### Running Both

```bash
# Terminal 1: Backend
cd ai-goal-based-agentic-ai
venv\Scripts\activate
uvicorn main:app --reload --port 8001

# Terminal 2: Frontend
cd ai-goal-based-agentic-ai/frontend
npm start
```

### Streamlit Demo (Legacy)

```bash
# Alternative UI using Streamlit
streamlit run ui.py
```

### Docker (Future)

Currently no Docker setup. To containerize:

```dockerfile
# Backend Dockerfile (example)
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## 15. Testing

### Test Files

| File | Purpose |
|------|---------|
| `backend_test.py` | Basic API endpoint tests |
| `comprehensive_backend_test.py` | Full backend coverage |
| `test_pdf_submission.py` | PDF upload and processing |
| `test_websocket.py` | WebSocket connection tests |

### Running Tests

```bash
# Activate venv
venv\Scripts\activate

# Run all tests
pytest

# Run specific test
pytest backend_test.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

### Test Results (Latest)

From `test_reports/iteration_1.json`:

```
Backend: 85% (API infrastructure complete, LLM integration needs valid key)
Frontend: 100% (all UI components and interactions working)

✅ Passed:
- Health check
- Job submission
- Job status retrieval
- WebSocket connection
- File persistence
- Frontend components
- CORS configuration

❌ Needs Attention:
- OpenAI API key validation (401 with placeholder key)
```

### Manual Testing Checklist

1. **Upload Flow**
   - [ ] PDF file drag & drop works
   - [ ] Job description validation (min 50 chars)
   - [ ] Template selector changes template
   - [ ] Submit button disabled until valid

2. **Processing Flow**
   - [ ] Agent timeline updates correctly
   - [ ] Live console shows messages
   - [ ] Progress bar increments
   - [ ] Retry attempts visible

3. **Results Flow**
   - [ ] ATS score displays correctly
   - [ ] Comparison shows before/after
   - [ ] Preview renders resume
   - [ ] Download produces valid PDF

---

## Appendix

### Quick Reference

```bash
# Start backend
uvicorn main:app --reload --port 8001

# Start frontend
cd frontend && npm start

# Check health
curl http://localhost:8001/api/

# Submit job (example)
curl -X POST http://localhost:8001/api/optimize-resume \
  -F "resume=@my_resume.pdf" \
  -F "job_description=Looking for a Python developer..." \
  -F "template=harvard"

# Check status
curl http://localhost:8001/api/status/{job_id}
```

### Key File Quick Links

| Purpose | File |
|---------|------|
| API entry point | `main.py` |
| Agent orchestration | `crew.py` |
| Planner agent | `agents/planner.py` |
| Executor agent | `agents/executor.py` |
| Critic agent | `agents/critic.py` |
| Job persistence | `utils/job_store.py` |
| ATS scoring | `utils/ats_scorer.py` |
| PDF generation | `services/pdf_service.py` |
| HTML rendering | `services/template_renderer.py` |
| Data schema | `schemas/resume_schema.py` |
| LLM config | `config/llm.py` |
| Template config | `config/template_contexts.py` |
| Frontend app | `frontend/src/App.js` |
| API client | `frontend/src/services/api.js` |
| Polling hook | `frontend/src/hooks/useJobPolling.js` |
| Requirements | `memory/PRD.md` |

### Contact & Support

For issues or questions:
1. Check this document first
2. Review `memory/PRD.md` for requirements
3. Check test reports in `test_reports/`
4. Review agent outputs in job JSON files

---

*End of Knowledge Transfer Document*
