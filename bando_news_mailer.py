# -*- coding: utf-8 -*-
"""
BANDO 뉴스(Eng) 페이지에서 이번 달 + 저번 달 게시물만 추출해
Gmail API로 HTML 메일 발송 (표 형식: Date | Title | Link)
- Selenium 제거: requests + BeautifulSoup 사용
- <a href="javascript:void(0)"> 문제 해결: onclick 안의 실제 URL(.pdf 등) 추출
- 여러 수신자 지원
"""

import os
import re
import html
import datetime
import base64
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
# 번역 라이브러리 (googletrans)
try:
    from googletrans import Translator
except ImportError:
    Translator = None

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# =====================[ 설정 ]=====================
URL = "https://www.bandogrp.com/eng/news/index.html"
# 스크립트 파일의 실제 위치를 기준으로 BASE_DIR 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SENDER_EMAIL = "drbd2022006@gmail.com"
RECEIVER_EMAILS = [  # 여러 명 추가 가능
    "jung.jae.hun@drbworld.com",
    "kim.jeong.yun@drbworld.com",
]

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")
SAVE_HTML_PATH = os.path.join(BASE_DIR, "temp", "bando_news.html")  # 디버그용 원본 HTML 저장
BASE_HOST = "https://www.bandogrp.com"
# ================================================


def get_credentials():
    """Gmail API 인증 토큰 로드/갱신"""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"credentials.json이 없습니다: {CREDENTIALS_FILE}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return creds


def extract_link_from_a(a_tag):
    """<a> 태그에서 실제 이동 링크를 추출"""
    if not a_tag:
        return None

    # 1) href 우선
    href = (a_tag.get("href") or "").strip()
    if href and not href.lower().startswith("javascript"):
        return urljoin(BASE_HOST, href)

    # 2) onclick 검사
    onclick = (a_tag.get("onclick") or "").strip()
    if onclick:
        m = re.search(r"['\"]\s*([^'\"]+?)\s*['\"]", onclick)
        if m:
            return urljoin(BASE_HOST, m.group(1))
        m2 = re.search(r"(https?://[^\s'\"()]+|/[^\s'\"()]+)", onclick)
        if m2:
            return urljoin(BASE_HOST, m2.group(1))

    # 3) data-* 속성 확인
    for key in ("data-href", "data-url", "data-link"):
        v = a_tag.get(key)
        if v:
            return urljoin(BASE_HOST, v.strip())

    return None


def scrape_and_filter_news(debug=True):
    """뉴스 페이지에서 이번 달 & 저번 달 기사만 추출"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        "Cache-Control": "no-cache",
    }
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()

    html_text = resp.text
    if debug:
        try:
            os.makedirs(os.path.dirname(SAVE_HTML_PATH), exist_ok=True)
            with open(SAVE_HTML_PATH, "w", encoding="utf-8") as f:
                f.write(html_text)
            print(f"[DEBUG] 원본 HTML 저장: {SAVE_HTML_PATH} (len={len(html_text)})")
        except Exception as e:
            print(f"[DEBUG] HTML 저장 실패: {e}")

    soup = BeautifulSoup(html_text, "html.parser")

    today = datetime.date.today()
    first_day_current_month = today.replace(day=1)
    first_day_previous_month = (first_day_current_month - datetime.timedelta(days=1)).replace(day=1)

    articles = []

    def try_collect(container):
        text = container.get_text(" ", strip=True)
        m = re.search(r"\b(\d{4}/\d{1,2}/\d{1,2})\b", text)
        a = container.find("a")
        if not (m and a):
            return
        date_str = m.group(1)
        try:
            d = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
        except ValueError:
            return
        if d >= first_day_previous_month:
            link = extract_link_from_a(a) or "N/A"
            title = a.get_text(strip=True)
            articles.append({"date": date_str, "title": title, "link": link})

    # 1) ul/li 구조
    for li in soup.select("ul li"):
        try_collect(li)

    # 2) table/tr 구조
    if not articles:
        for tr in soup.select("table tr"):
            try_collect(tr)

    # 중복 제거 + 최신순 정렬
    dedup = {(x["date"], x["title"], x["link"]): x for x in articles}
    articles = sorted(dedup.values(), key=lambda x: x["date"], reverse=True)

    print(f"[INFO] 추출된 게시물: {len(articles)}건")
    return articles


def create_email_body(articles):
    """HTML 본문: 날짜 | 제목 | 링크 표"""
    if not articles:
        return "<h1>Bando News</h1><p>이번 달과 저번 달 게시물이 없습니다.</p>"

    rows = []
    for a in articles:
        date = a["date"]
        title = html.escape(a["title"])
        link = a["link"]
        if link != "N/A":
            link_cell = f"<a href='{link}'>{link}</a>"
            title_cell = f"<a href='{link}'>{title}</a>"
        else:
            link_cell = "N/A"
            title_cell = title

        rows.append(
            f"<tr>"
            f"<td style='padding:6px 10px; white-space:nowrap;'>{date}</td>"
            f"<td style='padding:6px 10px;'>{title_cell}</td>"
            f"<td style='padding:6px 10px;'>{link_cell}</td>"
            f"</tr>"
        )

    table = (
        "<h1>Bando News (이번 달 & 저번 달)</h1>"
        "<table border='1' cellspacing='0' cellpadding='0' "
        "style='border-collapse:collapse; font-family:Arial,Helvetica,sans-serif; font-size:14px;'>"
        "<thead>"
        "<tr style='background:#f2f2f2;'>"
        "<th style='padding:8px 10px;'>Date</th>"
        "<th style='padding:8px 10px;'>Title</th>"
        "<th style='padding:8px 10px;'>Link</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(rows) +
        "</tbody>"
        "</table>"
    )
    return table


def send_email(creds, articles):
    """Gmail API로 HTML 메일 발송 (여러 수신자 지원, Gates+Bando)"""
    try:
        service = build("gmail", "v1", credentials=creds)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        bando_html = create_email_body(articles)
        body = (
            f"<h2>[자동화] 월간 뉴스 리포트 ({today_str})</h2>"
            f"<hr>"
            f"{bando_html}"
        )
        msg = MIMEText(body, "html", _charset="utf-8")
        msg["Subject"] = f"[자동화] Bando 월간 뉴스 리포트 ({today_str})"
        msg["From"] = SENDER_EMAIL
        msg["To"] = ", ".join(RECEIVER_EMAILS)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        print(f"[INFO] 이메일 발송 완료: Bando {len(articles)}건, 수신자: {msg['To']}")
    except HttpError as e:
        print(f"[ERROR] 이메일 전송 오류: {e}")


def main():
    print(f"--- {datetime.datetime.now()} --- 실행 시작 ---")
    try:
        creds = get_credentials()
    except Exception as e:
        print(f"[ERROR] 인증 실패: {e}")
        return

    articles = scrape_and_filter_news(debug=True)

    send_email(creds, articles)

    if not articles:
        print("[INFO] 보낼 게시물이 없습니다. (이번 달/저번 달 범위 없음)")
    print("--- 실행 종료 ---")


if __name__ == "__main__":
    main()
