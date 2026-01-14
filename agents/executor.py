from crewai import Agent

executor = Agent(
    role="Task Executor",
    goal="Execute the plan efficiently",
    backstory="Strong technical executor",
    verbose=True
)
