# 🤖 Goal-Based Agentic AI System

A production-style **multi-agent AI system** built using **CrewAI**, where intelligent agents collaborate to plan, execute, and review tasks — exposed via a FastAPI backend and demonstrated through a Streamlit UI.

This project showcases how modern **agentic AI architectures** can be designed with clean orchestration, extensibility, and real-world MLOps thinking.

---

## 🚀 What This Project Does

The system uses three collaborating agents:

- **Planner Agent** – breaks a user goal into clear, actionable steps  
- **Executor Agent** – executes the planned steps logically  
- **Critic Agent** – reviews results and suggests improvements  

Together they form a **goal-driven AI workflow** that mimics real decision pipelines used in production AI systems.

---

## 🧠 Key Features

- 🔁 **Multi-Agent Orchestration** using CrewAI  
- ⚙️ **Sequential Agent Flow**: Planner → Executor → Critic  
- 🌐 **FastAPI Backend** to expose agent workflows as an API  
- 🎨 **Streamlit Demo UI** to visualize agent collaboration  
- 🧩 **Extensible Architecture** designed for:
  - Preference alignment (DPO + PEFT – future phase)
  - Human-in-the-loop feedback
  - Tool-augmented agents  
- 🏗️ **MLOps-Friendly Design**
  - Runtime orchestration separated from training pipelines
  - Production-style modular structure

---


## 🖥️ Demo

### Streamlit UI
Users can:
1. Enter a task
2. Run the agents
3. See:
   - Planner output  
   - Executor output  
   - Critic review  
   - Final refined result  

### Backend
The FastAPI service runs the full multi-agent workflow and returns structured outputs for each agent stage.

---

##  Upgrade — Advanced Agentic Intelligence

- Integrated Self-RAG using LlamaIndex
- Hybrid retrieval pipeline + reranking
- Critic-guided retrieval loop to reduce hallucinations
- Built DPO fine-tuning pipeline for preference-aligned agents
- Improved reasoning depth & factual grounding

## 🧩 Tech Stack

- **Python 3.12**
- **CrewAI** – agent orchestration
- **FastAPI** – backend API
- **Streamlit** – demo UI
- **Requests** – UI ↔ API communication

---

## ⚙️ How to Run Locally

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd ai-goal-based-agentic-ai
