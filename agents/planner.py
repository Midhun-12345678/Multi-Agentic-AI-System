from crewai import Agent

planner = Agent(
    role="ATS Resume Strategist",
    goal="Analyze resume and job description to create an ATS optimization plan",
    backstory="Expert in ATS systems, recruiter screening, and keyword alignment",
    verbose=True
)
