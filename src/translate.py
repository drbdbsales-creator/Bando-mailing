import os
import logging
from typing import Optional
import requests

logger = logging.getLogger("gates_news.translate")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def translate_en_to_ko(text: str) -> Optional[str]:
    if not GEMINI_API_KEY:
        logger.info("GEMINI_API_KEY not set. Skipping translation.")
        return ""
    try:
        # Gemini API 예시 (실제 엔드포인트/파라미터는 문서 참고)
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": f"Summarize the following text in one sentence and then translate it into Korean: {text}"}]}],
            "generationConfig": {"temperature": 0.7}
        }
        resp = requests.post(f"{url}?key={GEMINI_API_KEY}", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        # 실제 응답 구조에 따라 파싱 필요
        ko = result["candidates"][0]["content"]["parts"][0]["text"]
        return ko.strip()
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return ""
