import streamlit as st
import requests

st.set_page_config(page_title="Multi-Agent AI Demo", layout="centered")

# ---------------- HEADER ----------------
st.title("🤖 Multi-Agent AI System")
st.write("Planner → Executor → Critic workflow powered by CrewAI")

st.divider()

# ---------------- INPUT ----------------
task = st.text_area(
    "Enter your task",
    placeholder="e.g. Create a 3-step plan to launch an AI startup",
    height=100
)

run_btn = st.button("🚀 Run Agents")

# ---------------- RUN ----------------
if run_btn:
    if not task.strip():
        st.warning("Please enter a task.")
    else:
        with st.spinner("Agents are working..."):
            try:
                res = requests.post(
                    "http://localhost:8000/run",
                    json={"task": task},
                    timeout=180
                )

                data = res.json()

                st.success("Done!")

                # ---------------- OUTPUT ----------------
                st.subheader("🗺 Planner Output")
                st.write(data.get("planner", "No output"))

                st.subheader("⚙ Executor Output")
                st.write(data.get("executor", "No output"))

                st.subheader("🧐 Critic Output")
                st.write(data.get("critic", "No output"))

                st.subheader("✅ Final Result")
                st.write(data.get("final", "No output"))

            except Exception as e:
                st.error(f"Something went wrong: {e}")

st.divider()
st.caption("Demo: Multi-Agent AI System | CrewAI + FastAPI + Streamlit")
