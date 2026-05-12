import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

THEMES = {
    "modern":        {"it": "Moderno",       "en": "Modern",        "emoji": "🏙️"},
    "rustic":        {"it": "Rustico",        "en": "Rustic",        "emoji": "🏡"},
    "industrial":    {"it": "Industriale",    "en": "Industrial",    "emoji": "🏭"},
    "boho":          {"it": "Boho",           "en": "Boho",          "emoji": "🌿"},
    "classic":       {"it": "Classico",       "en": "Classic",       "emoji": "🏛️"},
    "japanese":      {"it": "Giapponese",     "en": "Japanese",      "emoji": "🎋"},
    "mediterranean": {"it": "Mediterraneo",   "en": "Mediterranean", "emoji": "🌊"},
    "vintage":       {"it": "Vintage",        "en": "Vintage",       "emoji": "📻"},
    "scandinavian":  {"it": "Scandinavo",     "en": "Scandinavian",  "emoji": "🧊"},
    "minimalist":    {"it": "Minimalista",    "en": "Minimalist",    "emoji": "◻️"},
    "eclectic":      {"it": "Eclettico",      "en": "Eclectic",      "emoji": "🎨"},
}

ROOM_TYPES = {
    "bathroom":    {"label": "Bathroom",    "it": "Bagno",         "emoji": "🛁"},
    "bedroom":     {"label": "Bedroom",     "it": "Camera",        "emoji": "🛏️"},
    "kitchen":     {"label": "Kitchen",     "it": "Cucina",        "emoji": "🍳"},
    "living_room": {"label": "Living Room", "it": "Soggiorno",     "emoji": "🛋️"},
    "office":      {"label": "Office",      "it": "Ufficio",       "emoji": "💼"},
}

class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/designs.db")
    search_api_key: str = os.getenv("SEARCH_API_KEY", "")
    search_engine_id: str = os.getenv("SEARCH_ENGINE_ID", "")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    trend_report_interval: int = int(os.getenv("TREND_REPORT_INTERVAL", "100"))

settings = Settings()
