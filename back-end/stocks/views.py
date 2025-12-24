import json
import os
import redis
from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.db import connection
from elasticsearch import Elasticsearch

# 모델 임포트 (앱 이름에 맞게 확인 필요)
from .models import StockDailyReport

ES_URL = os.getenv("ES_BASE_URL", "http://elasticsearch:9200")
STOCKS_INDEX = os.getenv("STOCKS_INDEX", "stocks-kospi")

def _get_redis_client():
    return redis.Redis(host="redis", port=6379, decode_responses=True)

def _parse_range(range_str: str):
    mapping = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "1d": timedelta(days=1),
        "1w": timedelta(days=7),
        "1m": timedelta(days=30),
        "3m": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    return mapping.get(range_str, timedelta(days=1))

def search_stocks(request):
    q = (request.GET.get("q") or "").strip()
    size = int(request.GET.get("size") or 10)
    if not q:
        return JsonResponse({"items": []})

    es = Elasticsearch(ES_URL)
    body = {
        "size": size,
        "_source": ["code", "name", "std_code", "group_code"],
        "query": {
            "bool": {
                "should": [
                    {"prefix": {"code": q}},
                    {"match": {"name": {"query": q}}},
                    {"match_phrase_prefix": {"name": {"query": q}}},
                ],
                "minimum_should_match": 1
            }
        }
    }
    try:
        resp = es.search(index=STOCKS_INDEX, body=body, request_timeout=3)
        hits = resp.get("hits", {}).get("hits", [])
        items = [{"code": h["_source"]["code"], "name": h["_source"]["name"]} for h in hits]
        return JsonResponse({"items": items})
    except Exception as e:
        return JsonResponse({"items": [], "error": str(e)}, status=500)

def current_price(request, code: str):
    r = _get_redis_client()
    val = r.get(f"current_price:{code}")
    if not val:
        return JsonResponse({"code": code, "data": None, "message": "No cache"}, status=200)
    try:
        data = json.loads(val)
        return JsonResponse({
            "code": code,
            "price": data.get("price"),
            "change_rate": data.get("change_rate"),
            "volume": data.get("volume"),
            "timestamp": data.get("timestamp"),
        })
    except:
        return JsonResponse({"code": code, "raw": val})

def chart(request, code: str):
    """
    주가 데이터와 AI 리포트를 병합하여 반환
    """
    range_str = request.GET.get("range", "1w") # 기본 범위를 1주일로 확장
    delta = _parse_range(range_str)
    since = timezone.now() - delta

    # 1. 가격 데이터 조회 (Raw SQL)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT time, close, volume
            FROM stocks_stockprice
            WHERE stock_id = %s AND time >= %s
            ORDER BY time ASC
            """,
            [code, since]
        )
        price_rows = cursor.fetchall()

    # 2. AI 리포트 조회
    # 💡 근본 해결: 날짜 필터링 범위를 조금 더 여유 있게 잡거나 제거하여 
    # 데이터가 빈 값으로 나가는 것을 방지합니다.
    report_since = since.date() - timedelta(days=1) # 하루 더 전부터 조회
    
    reports = StockDailyReport.objects.filter(
        stock_id=code, 
        target_date__gte=report_since
    ).values('target_date', 'ai_summary', 'sentiment_avg')
    
    report_map = {}
    for r in reports:
        date_str = r['target_date'].strftime('%Y-%m-%d')
        report_map[date_str] = {
            "summary": r['ai_summary'],
            # Decimal 객체는 JSON 변환이 안되므로 float로 변환
            "sentiment": float(r['sentiment_avg']) if r['sentiment_avg'] is not None else 0.0
        }

    # 가격 데이터가 없을 경우 처리
    if not price_rows:
        return JsonResponse({
            "code": code, "range": range_str, "labels": [], 
            "price": [], "volume": [], "ai_reports": report_map,
            "sentiment": [], "flow": []
        })

    labels, prices, volumes = [], [], []
    for ts, price, volume in price_rows:
        labels.append(ts.isoformat())
        prices.append(float(price)) # Decimal 방지
        volumes.append(float(volume))

    return JsonResponse({
        "code": code, 
        "range": range_str, 
        "labels": labels,
        "price": prices, 
        "volume": volumes,
        "ai_reports": report_map, # 여기에 데이터가 담겨서 내려감
        "sentiment": [], 
        "flow": [],
    })