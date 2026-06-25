"""
Centralized configuration for genius-confuc-io.
"""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"
MAX_RETRIES = 3

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
