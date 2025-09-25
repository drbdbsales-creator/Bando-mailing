"""
이 스크립트는 gates.com 뉴스 페이지를 크롤링합니다. robots.txt 및 이용약관을 반드시 확인하세요. 과도한 요청은 금지됩니다.
"""
import os
import sys
import argparse
import logging
import datetime
from . import fetch, parse, translate, mailer, store
import csv

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("gates_news.main")


def main():
    parser = argparse.ArgumentParser(description="Gates News Crawler")
    parser.add_argument("--once", action="store_true", help="한 번만 실행")
    parser.add_argument("--since", type=int, default=7, help="며칠 이내 뉴스만")
    parser.add_argument("--max", type=int, default=20, help="최대 뉴스 건수")
    parser.add_argument("--lang", choices=["ko", "en"], default="ko", help="요약 언어")
    args = parser.parse_args()

    news_items = fetch.fetch_news()
    seen = store.load_seen_urls()
    new_items = []
    today = datetime.date.today().strftime("%Y%m%d")
    cutoff = datetime.datetime.now() - datetime.timedelta(days=args.since)
    for item in news_items:
        if item["url"] in seen:
            continue
        # 날짜 필드가 있으면 필터링, 없으면 모두 포함
        parsed = parse.parse_item(item)
        if args.lang == "ko":
            ko = translate.translate_en_to_ko(parsed["summary_en"])
            parsed["summary_ko"] = ko
        else:
            parsed["summary_ko"] = ""
        new_items.append(parsed)
        seen.add(item["url"])
        if len(new_items) >= args.max:
            break
    store.save_seen_urls(seen)
    if new_items:
        mailer.send_news_email(new_items, datetime.date.today().strftime("%Y-%m-%d"))
        out_path = os.path.join(os.path.dirname(__file__), "..", "out", f"gates_news_{today}.csv")
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "summary_en", "summary_ko", "url"])
            writer.writeheader()
            for row in new_items:
                writer.writerow(row)
        logger.info(f"Saved {len(new_items)} news to {out_path}")
    else:
        logger.info("No new news found.")

if __name__ == "__main__":
    main()
