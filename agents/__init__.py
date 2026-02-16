"""
Agent definitions for the Resume Optimizer.
Configured to use emergentintegrations for LLM access.
"""

import os
from crewai import Agent, LLM
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

# Get the emergent key
api_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY')

# Configure LLM using litellm with custom base_url for emergent
# The emergent key works with a proxy endpoint
llm = LLM(
    model="gpt-4o-mini",
    api_key=api_key,
    base_url="https://ai-gateway.emergent.sh/v1",  # Emergent proxy endpoint
    temperature=0.3
)

# Planner Agent
planner = Agent(
    role="ATS Resume Strategist",
    goal="Analyze resume and job description to create an ATS optimization plan",
    backstory="Expert in ATS systems, recruiter screening, and keyword alignment",
    llm=llm,
    verbose=True
)

# Executor Agent  
executor = Agent(
    role="Resume Optimization Executor",
    goal="Rewrite resume using ATS strategy while preserving truth and identity",
    backstory="Professional resume writer with hiring domain experience",
    llm=llm,
    verbose=True
)

# Critic Agent
critic = Agent(
    role="Hiring Quality Reviewer, Resume Formatter & Field Mapping Validator",
    goal="Validate 100% field mapping accuracy between original and optimized resume, ensure strict markdown format for ATS parsing",
    backstory="""Senior hiring manager with real interview experience and data validation expertise.
    Expert at:
    1. Cross-checking original resume vs optimized output for complete field mapping
    2. Validating all job titles, companies, projects, skills, and contact info are preserved
    3. Formatting resumes in clean markdown structure with ### headers, **bold** job titles, and - bullet points
    4. Ensuring zero data loss during optimization
    5. Providing detailed validation reports on field mapping accuracy

    You meticulously verify that every piece of information from the original resume
    appears in the optimized version - no missing jobs, no lost projects, no omitted skills.""",
    llm=llm,
    verbose=True
)
