# 📊 데이터 아키텍처 및 연관성 분석

## 현재 데이터 구조

### 1. **StockPrice 모델** (Django ORM)
```python
# back-end/stocks/models.py
class StockPrice(models.Model):
    time = models.DateTimeField()
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.BigIntegerField()
```
- **테이블명**: `stocks_stockprice`
- **용도**: 실시간/과거 데이터 모두 저장 가능
- **현재 상태**: 모델은 있지만 **사용되지 않음** ❌

### 2. **historical_prices 테이블** (Raw SQL)
```sql
CREATE TABLE historical_prices (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date TIMESTAMP NOT NULL,
    open_price DOUBLE PRECISION,
    high_price DOUBLE PRECISION,
    low_price DOUBLE PRECISION,
    close_price DOUBLE PRECISION,
    volume BIGINT,
    ...
)
```
- **테이블명**: `historical_prices`
- **용도**: FinanceDataReader로 수집한 과거 데이터 저장
- **현재 상태**: `collect_historical_data.py`에서만 사용 ✅

### 3. **실시간 데이터 흐름**
```
Kafka → stock_consumer.py → Redis (current_price:{code})
                              ↓
                         Django API (조회만)
```
- **저장 위치**: Redis만 (PostgreSQL 저장 주석 처리됨) ⚠️

## 🔍 문제점

1. **데이터 분리**: 
   - 과거 데이터: `historical_prices` (Raw SQL)
   - 실시간 데이터: Redis만 (PostgreSQL 미저장)

2. **연관성 부족**:
   - 실시간 데이터가 `historical_prices`에 자동 저장되지 않음
   - `StockPrice` 모델이 있지만 사용되지 않음

3. **중복 구조**:
   - `StockPrice` 모델과 `historical_prices` 테이블이 거의 동일한 구조

## 💡 개선 방안

### 방안 1: StockPrice 모델 통합 사용 (권장) ⭐

**장점**:
- Django ORM 사용 가능
- 실시간/과거 데이터 통합 관리
- 마이그레이션으로 스키마 관리

**구조**:
```
StockPrice 모델 (stocks_stockprice 테이블)
├── 과거 데이터: collect_historical_data.py → StockPrice 저장
└── 실시간 데이터: stock_consumer.py → StockPrice 저장
```

### 방안 2: historical_prices 테이블에 실시간 데이터도 저장

**장점**:
- 기존 구조 유지
- Raw SQL로 빠른 성능

**구조**:
```
historical_prices 테이블
├── 과거 데이터: collect_historical_data.py
└── 실시간 데이터: stock_consumer.py → historical_prices 저장
```

### 방안 3: 하이브리드 (현재 구조 유지 + 실시간 저장 추가)

**구조**:
```
historical_prices: 과거 데이터 (FinanceDataReader)
StockPrice: 실시간 데이터 (Kafka → PostgreSQL)
```

## 🎯 추천: 방안 1 (StockPrice 모델 통합)

### 이유:
1. Django 모델 사용으로 일관성 유지
2. ORM으로 코드 간결화
3. 실시간/과거 데이터 통합 관리
4. 마이그레이션으로 스키마 버전 관리

### 구현:
1. `collect_historical_data.py` → `StockPrice` 모델 사용
2. `stock_consumer.py` → `StockPrice` 모델에 실시간 데이터 저장
3. `stocks/views.py` → `StockPrice` 모델에서 조회
4. `historical_prices` 테이블 제거 (선택)

## 📋 현재 데이터 흐름도

```
[과거 데이터]
FinanceDataReader 
  → collect_historical_data.py
  → historical_prices 테이블 (Raw SQL)
  → stocks/views.py chart() API
  → StockChart.vue

[실시간 데이터]
Kafka
  → stock_consumer.py
  → Redis (current_price:{code})
  → stocks/views.py current_price() API
  → Dashboard.vue (실시간 표시)
  
  ❌ historical_prices에 저장 안됨
```

## 🔄 개선된 데이터 흐름도 (방안 1)

```
[과거 데이터]
FinanceDataReader 
  → collect_historical_data.py
  → StockPrice 모델 (stocks_stockprice)
  → stocks/views.py chart() API
  → StockChart.vue

[실시간 데이터]
Kafka
  → stock_consumer.py
  → Redis (current_price:{code}) [실시간 조회용]
  → StockPrice 모델 (stocks_stockprice) [영구 저장]
  → stocks/views.py chart() API (최근 데이터 포함)
  → StockChart.vue
```

