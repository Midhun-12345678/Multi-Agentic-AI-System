from crewai import Agent

critic = Agent(
    role="Quality Critic",
    goal="Review outputs and improve quality",
    backstory="Detail-oriented reviewer",
)
