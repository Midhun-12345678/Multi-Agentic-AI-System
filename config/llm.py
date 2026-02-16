import os

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.3))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2048))
