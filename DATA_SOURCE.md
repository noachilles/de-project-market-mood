# 📊 데이터 소스 정리

## 데이터 흐름 및 저장 위치

### 1. 뉴스 피드 (NewsFeed.vue)

**데이터 소스**: Elasticsearch `news` 인덱스

**API 엔드포인트**: `GET /api/news/?ticker={code}&size=5`

**데이터 구조**:
```json
{
  "ticker": "005930",
  "items": [
    {
      "title": "삼성전자 관련 뉴스 제목",
      "published_at": "2025-12-25T10:00:00",
      "sentiment_score": 0.65,
      "original_url": "https://news.example.com/005930/2025-12-25/news_id"
    }
  ],
  "count": 5
}
```

**저장 위치**:
- Elasticsearch 인덱스: `news`
- 생성 방법: `generate_dummy_news.py` 명령어로 더미 데이터 생성
- 필드: `title`, `published_at`, `sentiment_score`, `original_url`, `stock_codes`

**클릭 동작**: 뉴스 항목 클릭 시 `original_url`로 새 창에서 열림

---

### 2. 전날 분석 리포트 (WatchList의 YesterdayReportCard)

**데이터 소스**: PostgreSQL `StockDailyReport` 모델

**API 엔드포인트**: `GET /api/chart/{code}?range=1w` (응답의 `ai_reports` 필드)

**데이터 구조**:
```json
{
  "code": "005930",
  "range": "1w",
  "candles": [...],
  "ai_reports": {
    "2025-12-24": {
      "summary": "삼성전자의 2025-12-24 주요 뉴스 요약: 시장 동향 긍정적.",
      "sentiment": 0.65,
      "date": "2025-12-24"
    }
  }
}
```

**저장 위치**:
- PostgreSQL 테이블: `stocks_stockdailyreport`
- 생성 방법: `generate_dummy_news.py` 명령어로 생성
- 필드: `stock`, `target_date`, `ai_summary`, `sentiment_avg`

**표시 위치**: 좌측 WatchList 컴포넌트의 `YesterdayReportCard`

---

### 3. 주가 데이터 (StockChart.vue)

**데이터 소스**: PostgreSQL `StockPrice` 모델

**API 엔드포인트**: `GET /api/chart/{code}?range={range}`

**저장 위치**:
- PostgreSQL 테이블: `stocks_stockprice`
- 생성 방법:
  - 과거 데이터: `collect_historical_data.py` (FinanceDataReader 사용)
  - 실시간 데이터: `stock_consumer.py` (Kafka → Redis → StockPrice)

**필드**: `stock`, `time`, `open`, `high`, `low`, `close`, `volume`

---

### 4. 현재가 (Header, WatchList)

**데이터 소스**: 
1. **우선순위 1**: Redis (`current_price:{code}`)
2. **우선순위 2**: PostgreSQL `StockPrice` 모델의 마지막 데이터

**API 엔드포인트**: `GET /api/current-price/{code}`

**동작 방식**:
- Redis에 데이터가 있으면 즉시 반환
- Redis에 데이터가 없으면 StockPrice 모델에서 마지막 거래일 데이터 조회
- 마지막 거래일의 전체 거래량(volume) 합계 반환

**장 마감 후**: 마지막 거래일 데이터로 고정 표시

---

## 데이터 생성 명령어

```bash
# 1. 과거 주가 데이터 수집 (3개월치)
docker-compose exec backend python manage.py collect_historical_data --stock-code 005930 --months 3

# 2. 더미 뉴스 및 StockDailyReport 생성
docker-compose exec backend python manage.py generate_dummy_news --stock-code 005930 --news-per-day 2
```

---

## 데이터 흐름도

```
[과거 주가 데이터]
FinanceDataReader 
  → collect_historical_data.py
  → StockPrice 모델 (PostgreSQL)
  → /api/chart/{code} API
  → StockChart.vue

[실시간 주가 데이터]
Kafka
  → stock_consumer.py
  → Redis (current_price:{code}) [실시간 조회용]
  → StockPrice 모델 (PostgreSQL) [영구 저장]
  → /api/current-price/{code} API
  → Header, WatchList

[뉴스 데이터]
generate_dummy_news.py
  → Elasticsearch (news 인덱스)
  → /api/news/ API
  → NewsFeed.vue

[전날 분석 리포트]
generate_dummy_news.py
  → StockDailyReport 모델 (PostgreSQL)
  → /api/chart/{code} API (ai_reports 필드)
  → WatchList (YesterdayReportCard)
```

