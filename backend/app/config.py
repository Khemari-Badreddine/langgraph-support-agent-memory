import os
from dotenv import load_dotenv

load_dotenv()


# === Gemini API ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set in .env")

print("GEMINI_API_KEY =", GEMINI_API_KEY)

# Model config
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", 0.7))

# App config
DATABASE_URL = os.getenv("DATABASE_URL", "")