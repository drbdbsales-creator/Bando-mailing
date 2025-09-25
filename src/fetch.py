import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import List, Dict

SITEMAP_URL = "https://www.gates.com/sitemap.xml"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GatesNewsBot/1.0)"}

logger = logging.getLogger("gates_news.fetch")

def fetch_news() -> List[Dict]:
    """
    Fetches news articles by parsing the sitemap and then scraping each article page.
    """
    article_urls = []
    try:
        resp = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30, verify=False)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        for loc in soup.find_all("loc"):
            url = loc.get_text()
            if "/us/en/about-us/news/insights/" in url:
                article_urls.append(url)
    except Exception as e:
        logger.error(f"Sitemap fetch or parse error: {e}")
        return []

    logger.info(f"Found {len(article_urls)} article URLs in sitemap.")

    news = []
    for url in article_urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10, verify=False)
            resp.raise_for_status()
            article_soup = BeautifulSoup(resp.text, "html.parser")
            
            title = article_soup.find("title").get_text(strip=True)
            
            summary = ""
            meta_desc = article_soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                summary = meta_desc.get("content", "")

            if title and url:
                news.append({
                    "title": title,
                    "url": url,
                    "summary": summary
                })
            time.sleep(1) # Be respectful and don't hammer the server
        except Exception as e:
            logger.error(f"Error fetching article page {url}: {e}")
            
    return news