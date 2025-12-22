import json
from datetime import timedelta

from django.http import JsonResponse
from django.utils import timezone
from django.db import connection

import redis


def _get_redis_client():
    # docker-compose 기준: redis 호스트명은 "redis"
    return redis.Redis(host="redis", port=6379, decode_responses=True)


def current_price(request, code: str):
    """
    GET /api/current-price/{code}
    - Redis: current_price:{code} 조회
    """
    r = _get_redis_client()
    key = f"current_price:{code}"
    val = r.get(key)

    if not val:
        return JsonResponse(
            {"code": code, "data": None, "message": "No cached price in Redis"},
            status=404
        )

    try:
        data = json.loads(val)
    except Exception:
        # 혹시 value가 JSON이 아니면 그대로 반환
        data = {"raw": val}

    # 프론트 친화 형태로 고정
    return JsonResponse({
        "code": code,
        "price": data.get("price"),
        "change_rate": data.get("change_rate"),
        "volume": data.get("volume"),
        "timestamp": data.get("timestamp"),
    })


def _parse_range(range_str: str):
    """
    차트 범위 파라미터 → timedelta
    range: 1h | 6h | 1d | 1w | 1m | 3m | 1y
    """
    mapping = {
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "1d": timedelta(days=1),
        "1w": timedelta(days=7),
        "1m": timedelta(days=30),
        "3m": timedelta(days=90),
        "1y": timedelta(days=365),
    }
    return mapping.get(range_str, timedelta(days=1))  # default 1d


def chart(request, code: str):
    """
    GET /api/chart/{code}?range=1d
    - Postgres(Timescale)에서 stock_prices 조회
    - Vue/Chart.js가 바로 쓰기 좋은 형태로 반환
    """
    range_str = request.GET.get("range", "1d")
    delta = _parse_range(range_str)
    since = timezone.now() - delta

    # ✅ Timescale 조회 (raw SQL이 제일 단순/확실)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ts, price, volume
            FROM stock_prices
            WHERE code = %s AND ts >= %s
            ORDER BY ts ASC
            """,
            [code, since]
        )
        rows = cursor.fetchall()

    labels = []
    prices = []
    volumes = []

    for ts, price, volume in rows:
        # ts는 aware datetime일 수 있음 → ISO로 통일
        labels.append(ts.isoformat())
        prices.append(price)
        volumes.append(volume)

    return JsonResponse({
        "code": code,
        "range": range_str,
        "labels": labels,      # x축
        "price": prices,       # line
        "volume": volumes,     # bar 등으로 사용 가능
        # sentiment/flow는 아직 없으니 일단 빈 배열(프론트 깨짐 방지)
        "sentiment": [],
        "flow": [],
    })
