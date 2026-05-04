import os
from dotenv import load_dotenv

load_dotenv()


def get_openrouter_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return key

# Model config
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", 0.7))


CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000")
CORS_ORIGINS_LIST = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]

# App config
DATABASE_URL = os.getenv("DATABASE_URL", "")