# 🚀 빠른 시작 가이드 (빌드 문제 해결)

## 문제 해결: FinanceDataReader로 인한 빌드 실패

FinanceDataReader 패키지가 빌드 시 문제를 일으킬 수 있어, **requirements.txt에서 제거**하고 **런타임에 선택적으로 설치**하도록 변경했습니다.

## ✅ 해결된 빌드 방법

### 1단계: 빌드 (FinanceDataReader 없이)
```bash
# 이제 빌드가 성공할 것입니다
docker-compose build backend
```

### 2단계: 필요한 서비스 시작
```bash
docker-compose up -d postgres redis backend
```

### 3단계: FinanceDataReader 설치 (런타임)
```bash
# 컨테이너가 실행 중일 때 설치
docker-compose exec backend pip install FinanceDataReader
```

### 4단계: Step 1 실행
```bash
docker-compose exec backend python manage.py collect_historical_data
```

## 📋 전체 명령어 (한 번에 실행)

```bash
# 1. 빌드 (이제 성공할 것입니다!)
docker-compose build backend

# 2. 서비스 시작
docker-compose up -d postgres redis backend

# 3. FinanceDataReader 설치
docker-compose exec backend pip install FinanceDataReader

# 4. 데이터 수집 실행
docker-compose exec backend python manage.py collect_historical_data

# 5. 검증
docker-compose exec postgres psql -U ${POSTGRES_USER:-ssafyuser} -d ${POSTGRES_DB:-postgres} -c "
SELECT COUNT(*), MIN(trade_date), MAX(trade_date) 
FROM historical_prices 
WHERE stock_code = '005930';"
```

## 🔍 변경 사항

- ✅ `requirements.txt`에서 `FinanceDataReader` 제거
- ✅ 빌드 시 FinanceDataReader 없이 진행
- ✅ 런타임에 선택적으로 설치하도록 변경

이제 빌드가 성공할 것입니다!


