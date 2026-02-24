"""
Configuration settings for ADK BI Chatbot
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from this package root (adk-chatbot/) so it works no matter where the app is run from
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# Google Cloud / Gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Database
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Discord
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

# Gmail
GMAIL_OAUTH_CLIENT_ID = os.getenv("GMAIL_OAUTH_CLIENT_ID")
GMAIL_OAUTH_CLIENT_SECRET = os.getenv("GMAIL_OAUTH_CLIENT_SECRET")
GMAIL_RECIPIENT_EMAIL = os.getenv("GMAIL_RECIPIENT_EMAIL")

# Known dimension values (from database)
KNOWN_DIMENSIONS = {
    "ship_mode": ["First Class", "Second Class", "Standard Class", "Same Day"],
    "region": ["West", "East", "Central", "South"],
    "segment": ["Consumer", "Corporate", "Home Office"],
    "category": ["Technology", "Furniture", "Office Supplies"]
}

# ADK Configuration
MODEL_NAME = "openai/gpt-4o-mini"  # Using OpenAI GPT-4o Mini
MESSAGE_HISTORY_KEY = "message_history"