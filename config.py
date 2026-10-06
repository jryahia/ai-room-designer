import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

THEMES = {
    "modern":        {"it": "Moderno",       "en": "Modern",        "icon": "building-2"},
    "rustic":        {"it": "Rustico",        "en": "Rustic",        "icon": "house"},
    "industrial":    {"it": "Industriale",    "en": "Industrial",    "icon": "factory"},
    "boho":          {"it": "Boho",           "en": "Boho",          "icon": "leaf"},
    "classic":       {"it": "Classico",       "en": "Classic",       "icon": "landmark"},
    "japanese":      {"it": "Giapponese",     "en": "Japanese",      "icon": "flower-2"},
    "mediterranean": {"it": "Mediterraneo",   "en": "Mediterranean", "icon": "waves"},
    "vintage":       {"it": "Vintage",        "en": "Vintage",       "icon": "radio"},
    "scandinavian":  {"it": "Scandinavo",     "en": "Scandinavian",  "icon": "snowflake"},
    "minimalist":    {"it": "Minimalista",    "en": "Minimalist",    "icon": "square"},
    "eclectic":      {"it": "Eclettico",      "en": "Eclectic",      "icon": "palette"},
}

ROOM_TYPES = {
    "bathroom":    {"label": "Bathroom",    "it": "Bagno",         "icon": "bath"},
    "bedroom":     {"label": "Bedroom",     "it": "Camera",        "icon": "bed-double"},
    "kitchen":     {"label": "Kitchen",     "it": "Cucina",        "icon": "cooking-pot"},
    "living_room": {"label": "Living Room", "it": "Soggiorno",     "icon": "sofa"},
    "office":      {"label": "Office",      "it": "Ufficio",       "icon": "briefcase"},
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
