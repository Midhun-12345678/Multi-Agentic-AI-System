from crewai import Agent

executor = Agent(
    role="Resume Optimization Executor",
    goal="Rewrite resume using ATS strategy while preserving truth and identity",
    backstory="Professional resume writer with hiring domain experience",
    verbose=True
)
