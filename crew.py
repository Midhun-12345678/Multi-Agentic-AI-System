from crewai import Crew, Task
from agents.planner import planner
from agents.executor import executor
from agents.critic import critic


def run_crew(user_input: str):
    """
    Run the multi-agent crew to plan, execute, and review tasks.
    """
    plan_task = Task(
        description=f"Create a step-by-step plan for: {user_input}",
        expected_output="A detailed step-by-step execution plan with clear tasks, sequence, responsibilities, and expected outcomes in numbered bullet points.",
        agent=planner
    )

    exec_task = Task(
        description="""Execute the plan created by the planner. 
        Follow each step precisely and provide the complete results of execution.""",
        expected_output="Complete execution results of the plan, including outputs from each step, any issues encountered, and final deliverables.",
        agent=executor,
        context=[plan_task]  # Uses planner's output as context
    )

    review_task = Task(
        description="""Review the execution results from the executor and planner. 
        Identify improvements, errors, or optimizations. Provide a final improved output.""",
        expected_output="A comprehensive review with identified issues, suggested improvements, and a finalized improved output or next steps.",
        agent=critic,
        context=[plan_task, exec_task]  # Uses both previous tasks as context
    )

    crew = Crew(
        agents=[planner, executor, critic],
        tasks=[plan_task, exec_task, review_task],
        verbose=True,
        process="sequential"  # Ensures tasks run in order
    )

    result = crew.kickoff()
    return result
