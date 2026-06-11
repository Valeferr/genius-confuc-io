"""
Configurazione centralizzata per genius-confuc-io
"""
import os

# API Keys
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Impostazioni LLM
DEFAULT_MODEL = "gpt-4o"
USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# Impostazioni Orchestrator
MAX_RETRIES = 3
