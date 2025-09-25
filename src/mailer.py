import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict

logger = logging.getLogger("gates_news.mailer")

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_TLS = os.getenv("SMTP_TLS", "true").lower() == "true"

FROM_ADDR = "drbdbsales@gmail.com"
TO_ADDR = "jung.jae.hun@drbworld.com"


def send_news_email(news_items: List[Dict], date_str: str):
    subject = f"[Gates News] 새 소식 {len(news_items)}건 ({date_str})"
    html = "<h3>Gates News</h3><table border='1'><tr><th>Title</th><th>Summary(EN)</th><th>Summary(KO)</th><th>URL</th></tr>"
    for item in news_items:
        html += f"<tr><td>{item['title']}</td><td>{item['summary_en']}</td><td>{item.get('summary_ko','')}</td><td><a href='{item['url']}'>{item['url']}</a></td></tr>"
    html += "</table>"
    msg = MIMEMultipart()
    msg['From'] = FROM_ADDR
    msg['To'] = TO_ADDR
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    try:
        if SMTP_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_ADDR, TO_ADDR, msg.as_string())
        server.quit()
        logger.info(f"Email sent: {subject}")
    except Exception as e:
        logger.error(f"Email send error: {e}")
