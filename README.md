# Gates News Crawler

이 스크립트는 gates.com 뉴스 페이지를 주기적으로 크롤링하여 최신 소식을 이메일로 발송합니다.

## 사용법

1. 의존성 설치
```
pip install -r requirements.txt
```

2. 환경변수 또는 .env 파일 설정
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=drbd2022006@gmail.com
SMTP_PASS=앱비밀번호
SMTP_TLS=true
GEMINI_API_KEY=구글_Gemini_API_키(선택)
```

3. 실행 예시
```
python -m src.main --once --since 3 --max 10 --lang ko
```

- `--once`: 한 번만 실행
- `--since DAYS`: 최근 DAYS일 이내 뉴스만
- `--max N`: 최대 N건
- `--lang ko|en`: 요약 언어

4. 크론탭 예시 (6시간마다 실행)
```
0 */6 * * * cd /path/to/Market sensing && python -m src.main --since 3 --max 10 --lang ko
```

## 출력 파일
- `out/gates_news_YYYYMMDD.csv` (UTF-8, 헤더 포함)

## 데이터 중복 방지
- 이미 보낸 뉴스 URL은 `data/news_seen.json`에 저장되어 재발송되지 않습니다.

## 라이선스/법적 안내
- gates.com의 robots.txt 및 이용약관을 반드시 확인하세요. 과도한 요청은 금지됩니다.

## 기타
- Gmail SMTP는 앱 비밀번호(2단계 인증 필요)가 없으면 동작하지 않을 수 있습니다. 불가 시 SendGrid 등 대체 SMTP를 환경변수로 설정해 주세요.
