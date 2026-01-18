from crewai import Crew, Task
from agents.planner import planner
from agents.executor import executor
from agents.critic import critic

from rag.loader import load_documents
from rag.indexer import build_index
from rag.retriever import build_retriever
from rag.self_rag import self_rag_loop


# ---------- RAG SETUP (runs once) ----------
documents = load_documents("data/docs")
index = build_index(documents)
retriever = build_retriever(index)


def run_crew(user_input: str):
    """
    Run the multi-agent crew with Self-RAG + Planner → Executor → Critic
    """

    # ---------- SELF-RAG CONTEXT ----------
    context = self_rag_loop(user_input, retriever, critic)

    # ---------- TASK 1 ----------
    plan_task = Task(
        description=f"""
        Using the following context:
        ---------------------------
        {context}

        Create a step-by-step plan for:
        {user_input}
        """,
        expected_output="A detailed step-by-step execution plan.",
        agent=planner
    )

    # ---------- TASK 2 ----------
    exec_task = Task(
        description="Execute the plan created by the planner.",
        expected_output="Complete execution results of the plan.",
        agent=executor,
        context=[plan_task]
    )

    # ---------- TASK 3 ----------
    review_task = Task(
        description="Review the execution and improve it.",
        expected_output="A reviewed and improved final output.",
        agent=critic,
        context=[plan_task, exec_task]
    )

    # ---------- CREW ----------
    crew = Crew(
        agents=[planner, executor, critic],
        tasks=[plan_task, exec_task, review_task],
        verbose=True,
        process="sequential"
    )

    # ---------- RUN ----------
    final_result = crew.kickoff()

    # ---------- SAFE OUTPUT ----------
    planner_out = plan_task.output or "No planner output"
    executor_out = exec_task.output or "No executor output"
    critic_out = review_task.output or "No critic output"

    return {
        "planner": str(planner_out),
        "executor": str(executor_out),
        "critic": str(critic_out),
        "final": str(final_result)
    }
