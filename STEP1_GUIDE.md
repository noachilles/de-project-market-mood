# Step 1: 과거 데이터 확보 (FinanceDataReader) - 실행 가이드

## 📋 개요
FinanceDataReader를 사용하여 삼성전자(005930)의 최근 1년치 일봉 데이터(OHLCV)를 수집하고 PostgreSQL의 `historical_prices` 테이블에 저장합니다.

## 🚀 실행 방법

### 1. 환경 준비

#### 1-1. Docker 컨테이너 시작 (필요한 서비스만)
```bash
# Step 1에 필요한 서비스만 시작
docker-compose up -d postgres redis backend
```

#### 1-2. FinanceDataReader 패키지 설치 (필수)
```bash
# FinanceDataReader는 requirements.txt에서 제외되어 있으므로 수동 설치 필요
docker-compose exec backend pip install FinanceDataReader

# 설치 확인
docker-compose exec backend pip list | grep -i finance
```

### 2. 데이터 수집 실행

#### 2-1. 기본 실행 (삼성전자 005930, 최근 1년)
```bash
docker-compose exec backend python manage.py collect_historical_data
```

#### 2-2. 옵션 사용
```bash
# 다른 종목 코드로 실행
docker-compose exec backend python manage.py collect_historical_data --stock-code 000660

# 다른 기간으로 실행 (예: 최근 2년)
docker-compose exec backend python manage.py collect_historical_data --years 2
```

## ✅ 검증 방법

### 1. 스크립트 실행 결과 확인

스크립트 실행 시 다음과 같은 출력을 확인할 수 있습니다:

```
[005930] 종목의 최근 1년치 일봉 데이터 수집을 시작합니다...
✅ historical_prices 테이블이 이미 존재합니다.
데이터 수집 기간: 2024-01-01 ~ 2025-01-01
✅ 데이터 수집 완료!
   - 저장된 레코드: 250개
   - 건너뛴 레코드: 0개
   - 오류 발생: 0개
   - 총 수집 데이터: 250개

📊 저장된 데이터 통계:
   - 총 레코드 수: 250개
   - 최초 날짜: 2024-01-02 00:00:00+00:00
   - 최신 날짜: 2024-12-31 00:00:00+00:00
   - Volume 누락: 0개
```

### 2. 데이터베이스 직접 조회

```bash
# PostgreSQL 컨테이너에 접속
docker-compose exec postgres psql -U ${POSTGRES_USER:-ssafyuser} -d ${POSTGRES_DB:-postgres}

# historical_prices 테이블 조회
SELECT 
    stock_code,
    trade_date,
    open_price,
    high_price,
    low_price,
    close_price,
    volume
FROM historical_prices
WHERE stock_code = '005930'
ORDER BY trade_date DESC
LIMIT 10;

# 통계 확인
SELECT 
    COUNT(*) as total_records,
    MIN(trade_date) as earliest_date,
    MAX(trade_date) as latest_date,
    COUNT(CASE WHEN volume IS NULL THEN 1 END) as missing_volume_count
FROM historical_prices
WHERE stock_code = '005930';
```

### 3. Django Shell을 통한 검증

```bash
# Django shell 접속
docker-compose exec backend python manage.py shell

# Python 코드로 검증
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*), MIN(trade_date), MAX(trade_date),
               COUNT(CASE WHEN volume IS NULL THEN 1 END) as missing_volume
        FROM historical_prices
        WHERE stock_code = '005930'
    """)
    result = cursor.fetchone()
    print(f"총 레코드: {result[0]}, 최초 날짜: {result[1]}, 최신 날짜: {result[2]}, Volume 누락: {result[3]}")
```

### 4. SQL 쿼리로 빠른 확인

```bash
# 한 줄로 확인
docker-compose exec postgres psql -U ${POSTGRES_USER:-ssafyuser} -d ${POSTGRES_DB:-postgres} -c "
SELECT 
    COUNT(*) as total,
    MIN(trade_date) as earliest,
    MAX(trade_date) as latest,
    COUNT(CASE WHEN volume IS NULL THEN 1 END) as missing_volume
FROM historical_prices 
WHERE stock_code = '005930';"
```

## 🔍 체크 포인트

1. ✅ **Volume 데이터 누락 확인**: 스크립트 실행 시 volume이 NULL인 경우 경고 메시지가 출력됩니다.
2. ✅ **중복 데이터 방지**: `ON CONFLICT` 절을 사용하여 동일한 날짜의 데이터가 중복 저장되지 않도록 처리했습니다.
3. ✅ **에러 핸들링**: 각 레코드 저장 시 예외가 발생해도 다음 레코드 처리를 계속합니다.

## 🐛 문제 해결

### 문제: "No module named 'FinanceDataReader'"
**해결**: 
```bash
docker-compose exec backend pip install FinanceDataReader
```

### 문제: "relation 'historical_prices' does not exist"
**해결**: 스크립트가 자동으로 테이블을 생성합니다. 수동으로 생성하려면:
```bash
docker-compose exec postgres psql -U ${POSTGRES_USER:-ssafyuser} -d ${POSTGRES_DB:-postgres} -c "
CREATE TABLE IF NOT EXISTS historical_prices (
    id BIGSERIAL PRIMARY KEY,
    stock_code VARCHAR(10) NOT NULL,
    trade_date TIMESTAMP NOT NULL,
    open_price DOUBLE PRECISION,
    high_price DOUBLE PRECISION,
    low_price DOUBLE PRECISION,
    close_price DOUBLE PRECISION,
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code, trade_date)
);"
```

### 문제: "종목 정보가 없습니다"
**해결**: 스크립트가 자동으로 Stock 테이블에 종목 정보를 생성합니다.

### 문제: "FinanceDataReader 패키지를 찾을 수 없습니다"
**해결**: 
```bash
# 방법 1: 직접 설치
docker-compose exec backend pip install FinanceDataReader

# 방법 2: requirements.txt 확인 후 재빌드
docker-compose build backend
```

## 📝 다음 단계

Step 1이 완료되면 다음을 확인하세요:
- [ ] historical_prices 테이블에 데이터가 정상적으로 저장되었는지
- [ ] volume 데이터가 누락되지 않았는지
- [ ] 최근 1년치 데이터가 모두 수집되었는지

검증이 완료되면 **Step 2: 캔들 차트 고도화**로 진행하세요.

