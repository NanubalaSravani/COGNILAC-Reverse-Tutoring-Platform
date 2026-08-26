import os
from dotenv import load_dotenv

load_dotenv()

CHALLENGE_VERTICAL = "AI Reverse-Tutoring & Adaptive Socratic STEM Learning"
MODEL_NAME = "gemini-2.5-flash"

PRESET_TOPICS = {
    "🌱 Photosynthesis": {
        "title": "Photosynthesis",
        "description": "How green plants turn sunlight, water, and carbon dioxide into food and oxygen.",
        "starter_question": "Hey Teacher! I know plants need water and sun, but how do they actually make their own food inside their leaves?",
        "level_1_focus": "Basic concept of plants making food using light",
    },
    "🤖 Machine Learning": {
        "title": "Machine Learning",
        "description": "How computers learn from data and examples instead of explicit programming.",
        "starter_question": "Hey Teacher! My friend says computers can learn like humans now. How can a computer learn if it doesn't have a brain?",
        "level_1_focus": "How computers recognize patterns from data",
    },
    "🌐 Computer Networks": {
        "title": "Computer Networks",
        "description": "How computers send messages, websites, and games across the internet.",
        "starter_question": "Hey Teacher! When I click play on YouTube, how does the video travel from far away right onto my screen so fast?",
        "level_1_focus": "Data transfer across connected computers",
    },
    "🔐 Cryptography": {
        "title": "Cryptography",
        "description": "How secret codes and encryption keep passwords and messages safe.",
        "starter_question": "Hey Teacher! How do secret codes work on the internet so hackers can't steal my passwords?",
        "level_1_focus": "Scrambling and unlocking secret messages",
    },
}

DEFAULT_TOPIC = "Photosynthesis"

def find_preset_topic(topic_name: str) -> dict:
    """Find preset topic configuration matching title or key safely."""
    if not topic_name:
        return None
    clean_search = topic_name.strip().lower()
    for key, data in PRESET_TOPICS.items():
        if key.lower() == clean_search or data["title"].lower() == clean_search or clean_search in key.lower():
            return data
    return None

def get_api_key(ui_key: str = None) -> str:
    """Retrieve Gemini API Key prioritizing UI entry, then environment."""
    if ui_key and ui_key.strip():
        return ui_key.strip()
    env_key = os.getenv("GEMINI_API_KEY", "")
    return env_key.strip()

