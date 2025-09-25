import json
import os
import logging
from typing import Set

logger = logging.getLogger("gates_news.store")
SEEN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "news_seen.json")


def load_seen_urls() -> Set[str]:
    if not os.path.exists(SEEN_PATH):
        return set()
    try:
        with open(SEEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data)
    except Exception as e:
        logger.error(f"Failed to load seen URLs: {e}")
        return set()


def save_seen_urls(urls: Set[str]):
    try:
        with open(SEEN_PATH, "w", encoding="utf-8") as f:
            json.dump(list(urls), f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Failed to save seen URLs: {e}")
