import logging
from typing import Dict

logger = logging.getLogger("gates_news.parse")

def parse_item(item: Dict) -> Dict:
    title = item.get("title", "")
    url = item.get("url", "")
    summary_en = item.get("summary", "")
    # summary_en은 25~40단어로 제한
    words = summary_en.split()
    if len(words) > 40:
        summary_en = " ".join(words[:40]) + "..."
    elif len(words) < 25:
        summary_en = summary_en  # 그대로 둠
    return {
        "title": title,
        "url": url,
        "summary_en": summary_en
    }
