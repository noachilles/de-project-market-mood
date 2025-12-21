from django.http import JsonResponse
from core.utils.redis_client import get_redis_client
from stocks.services import get_latest_price_from_db

def current_price(request, stock_code: str):
    r = get_redis_client()
    redis_key = f"price:{stock_code}"

    # 1️⃣ Redis 조회
    cached = r.get(redis_key)

    if cached is not None:
        return JsonResponse({
            "stock_code": stock_code,
            "price": float(cached),
            "source": "redis",
        })

    # 2️⃣ Redis miss → TimescaleDB 조회
    latest = get_latest_price_from_db(stock_code)

    if latest is not None:
        # 3️⃣ Redis에 캐시 저장 (TTL 5초)
        r.setex(redis_key, 5, str(latest))

        return JsonResponse({
            "stock_code": stock_code,
            "price": float(latest),
            "source": "timescaledb",
        })

    # 4️⃣ DB에도 없음
    return JsonResponse(
        {
            "stock_code": stock_code,
            "price": None,
            "source": "not_found"
        },
        status=404
    )
