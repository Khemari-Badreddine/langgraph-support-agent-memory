import os
from dotenv import load_dotenv

load_dotenv()


# === Gemini API ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in .env")

# Model config
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", 0.7))

# App config
DATABASE_URL = os.getenv("DATABASE_URL", "")