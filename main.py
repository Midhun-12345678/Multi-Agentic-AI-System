import os
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["CREWAI_TELEMETRY_DISABLED"] = "true"
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from crew import run_crew
app = FastAPI()

@app.post("/run")
def run_agents(payload: dict):
    user_input = payload.get("task")
    result = run_crew(user_input)
    return {"result": result}
