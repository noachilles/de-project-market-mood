# Spark Job 실행 명령어 가이드

## Windows Git Bash 환경에서 실행 시 주의사항

Windows Git Bash에서는 경로와 따옴표가 잘못 해석될 수 있으므로, **컨테이너 내부로 직접 진입**하는 방법을 권장합니다.

## ✅ 권장 방법: 컨테이너 내부로 진입

**중요**: 먼저 Spark 컨테이너를 재빌드해야 합니다:
```bash
docker-compose build spark-master spark-worker
docker-compose restart spark-master spark-worker
```

```bash
# 1. 컨테이너 내부로 진입
docker-compose exec spark-master bash

# 2. 컨테이너 내부에서 실행 (news_content_crawler.py)
# Dockerfile에서 이미 다운로드한 JAR 파일 사용
/opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/elasticsearch-spark-30_2.12-8.11.0.jar \
  /app/jobs/news_content_crawler.py

# 3. 컨테이너 내부에서 실행 (news_ai_batch.py, 날짜 지정)
/opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark/jars/elasticsearch-spark-30_2.12-8.11.0.jar \
  /app/jobs/news_ai_batch.py 2024-01-15
```

## 대안: 스크립트 파일 사용

```bash
# 스크립트 파일 실행 (컨테이너 내부에서)
docker-compose exec spark-master bash /app/run_news_crawler.sh
docker-compose exec spark-master bash /app/run_news_ai_batch.sh 2024-01-15
```

## Windows CMD/PowerShell에서 실행 (대안)

```cmd
docker-compose exec spark-master bash -c "/opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0 /app/jobs/news_content_crawler.py"
```

## 4. 검증 명령어

### Elasticsearch 데이터 확인
```bash
curl -X GET "http://localhost:9200/news-enriched/_search?pretty" -H 'Content-Type: application/json' -d'{"size": 5, "query": {"match_all": {}}}'
```

### PostgreSQL 리포트 확인
```bash
docker-compose exec backend python manage.py shell -c "from stocks.models import StockDailyReport; reports = StockDailyReport.objects.all().order_by('-target_date')[:5]; [print(f'{r.target_date}: {r.ai_summary[:100]}...') for r in reports]"
```

