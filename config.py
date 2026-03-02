import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

GOOGLE_CLIENT_SECRET_FILE = "credentials.json"
GOOGLE_TOKEN_FILE = "token.pickle"
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
