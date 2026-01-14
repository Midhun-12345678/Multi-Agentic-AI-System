from crewai import Agent

planner = Agent(
    role="Task Planner",
    goal="Break user request into clear actionable steps",
    backstory="Expert in structuring complex tasks",
    verbose=True
)
