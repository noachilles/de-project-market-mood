# Step 2: 캔들 차트 고도화 - 구현 완료

## ✅ 구현 완료 사항

### 1. 백엔드 API 수정
- **`/api/chart/{code}?range=1w`**: `historical_prices` 테이블에서 OHLCV 데이터 조회
- 캔들 차트 형식으로 데이터 반환 (o, h, l, c, v)
- 날짜 정보 포함 (뉴스 조회용)

### 2. 뉴스 API 추가
- **`/api/news/by-date/?ticker=005930&date=2024-12-25`**: 특정 날짜의 뉴스 조회
- Elasticsearch에서 해당 날짜의 뉴스 검색
- 최대 5개 뉴스 반환

### 3. 프론트엔드 캔들 차트 구현
- **StockChart.vue**: `chartjs-chart-financial`을 사용한 캔들 차트
- **범위**: 1W, 1M, 3M 지원
- **호버 기능**: 캔들에 마우스를 올리면:
  - OHLC 정보 표시
  - 해당 날짜의 Elasticsearch 뉴스 제목 표시 (최대 3개)

## 🚀 테스트 방법

### 1. 더미 뉴스 데이터 생성 (필수!)

```bash
# historical_prices 테이블의 날짜를 기반으로 더미 뉴스 생성
docker-compose exec backend python manage.py generate_dummy_news

# 옵션 사용
docker-compose exec backend python manage.py generate_dummy_news --stock-code 005930 --news-per-day 3
```

### 2. 백엔드 API 테스트

```bash
# 캔들 데이터 조회
curl "http://localhost:8000/api/chart/005930?range=1w"

# 뉴스 조회
curl "http://localhost:8000/api/news/by-date/?ticker=005930&date=2024-12-25"
```

### 2. 프론트엔드 확인

1. 브라우저에서 `http://localhost` 접속
2. 대시보드에서 StockChart 컴포넌트 확인
3. 1W, 1M, 3M 버튼 클릭하여 캔들 차트 확인
4. 캔들에 마우스 호버하여 뉴스 제목 확인

## 📋 구현 세부사항

### 백엔드 (`back-end/stocks/views.py`)
- `chart()` 함수: `historical_prices` 테이블에서 OHLCV 조회
- 날짜 범위에 따라 데이터 필터링
- 캔들 형식으로 데이터 변환

### 백엔드 (`back-end/news/views.py`)
- `news_by_date()` 함수: Elasticsearch에서 날짜별 뉴스 조회
- ticker와 date 파라미터로 필터링
- 최대 5개 뉴스 반환

### 프론트엔드 (`front-end/src/components/dashboard/StockChart.vue`)
- `chartjs-chart-financial` 플러그인 사용
- 실시간 모드와 캔들 차트 모드 분리
- 호버 시 비동기로 뉴스 로드
- 뉴스 캐시 기능 (같은 날짜 재조회 방지)

### 프론트엔드 (`front-end/src/services/stocks.js`)
- `fetchChart()`: 캔들 데이터 조회
- `fetchNewsByDate()`: 날짜별 뉴스 조회

## 🔍 체크 포인트

- [x] 1W, 1M, 3M 범위의 캔들 차트 구현
- [x] 호버 시 OHLC 정보 표시
- [x] 호버 시 해당 날짜의 뉴스 제목 표시
- [x] Elasticsearch 연동
- [x] 에러 핸들링

## 📝 다음 단계

Step 2가 완료되었습니다! 이제 **Step 3: 실시간 알람 시스템**으로 진행할 수 있습니다.

