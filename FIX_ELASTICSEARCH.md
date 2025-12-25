# 🔧 Elasticsearch 디스크 공간 부족 해결 가이드

## 문제
```
TOO_MANY_REQUESTS/12/disk usage exceeded flood-stage watermark, index has read-only-allow-delete block
```

## 해결 방법

### 방법 1: 기존 인덱스 삭제 후 재생성 (권장)

```bash
# 1. 기존 news 인덱스 삭제
docker-compose exec elasticsearch curl -X DELETE "http://localhost:9200/news"

# 2. 더미 뉴스 재생성
docker-compose exec backend python manage.py generate_dummy_news
```

### 방법 2: Read-only 모드 해제

```bash
# Read-only 모드 해제
docker-compose exec elasticsearch curl -X PUT "http://localhost:9200/news/_settings" \
  -H 'Content-Type: application/json' \
  -d '{"index.blocks.read_only_allow_delete": null}'

# 더미 뉴스 재생성
docker-compose exec backend python manage.py generate_dummy_news
```

### 방법 3: Elasticsearch 데이터 볼륨 삭제 (완전 초기화)

```bash
# Elasticsearch 컨테이너 중지
docker-compose stop elasticsearch

# 데이터 볼륨 삭제
rm -rf ./data/volumes/es-data/*

# Elasticsearch 재시작
docker-compose up -d elasticsearch

# 잠시 대기 (초기화 시간)
sleep 10

# 더미 뉴스 생성
docker-compose exec backend python manage.py generate_dummy_news
```

### 방법 4: 배치 크기 줄이기

더미 뉴스 생성 시 하루당 뉴스 개수를 줄입니다:

```bash
# 하루당 1개만 생성
docker-compose exec backend python manage.py generate_dummy_news --news-per-day 1
```

## 빠른 해결 (한 번에 실행)

```bash
# 기존 인덱스 삭제 및 재생성
docker-compose exec elasticsearch curl -X DELETE "http://localhost:9200/news" && \
docker-compose exec backend python manage.py generate_dummy_news --news-per-day 1
```

## 검증

```bash
# 생성된 뉴스 확인
curl "http://localhost:9200/news/_count?q=stock_codes:005930"

# 특정 날짜 뉴스 확인
curl "http://localhost:8000/api/news/by-date/?ticker=005930&date=2024-12-25"
```


