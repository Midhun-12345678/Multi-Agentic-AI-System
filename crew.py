from crewai import Crew, Task
from agents.planner import planner
from agents.executor import executor
from agents.critic import critic


def run_crew(user_input: str):
    """
    Run the multi-agent crew to plan, execute, and review tasks.
    """

    # --- Define Tasks ---
    plan_task = Task(
        description=f"Create a step-by-step plan for: {user_input}",
        expected_output="A detailed step-by-step execution plan.",
        agent=planner
    )

    exec_task = Task(
        description="Execute the plan created by the planner.",
        expected_output="Complete execution results of the plan.",
        agent=executor,
        context=[plan_task]
    )

    review_task = Task(
        description="Review the execution and improve it.",
        expected_output="A reviewed and improved final output.",
        agent=critic,
        context=[plan_task, exec_task]
    )

    # --- Create Crew ---
    crew = Crew(
        agents=[planner, executor, critic],
        tasks=[plan_task, exec_task, review_task],
        verbose=True,
        process="sequential"
    )

    # --- Run ---
    final_result = crew.kickoff()

    # --- Safely extract outputs ---
    planner_out = plan_task.output or "No planner output"
    executor_out = exec_task.output or "No executor output"
    critic_out = review_task.output or "No critic output"

    return {
        "planner": str(planner_out),
        "executor": str(executor_out),
        "critic": str(critic_out),
        "final": str(final_result)
    }
