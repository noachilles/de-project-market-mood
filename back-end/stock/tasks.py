from celery import shared_task
import requests
from django.conf import settings
from django.core.cache import cache
from .utils_kis import get_common_headers
from .models import StockPrice  # 미리 정의했다고 가정

@shared_task(bind=True, max_retries=3)
def fetch_current_price(self, ticker_code):
    """
    주식 현재가 조회 (국내주식 기준)
    """
    # 1. API 설정
    url = f"{settings.KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id = "FHKST01010100" # 주식 현재가 시세 TR ID
    
    headers = get_common_headers(tr_id)
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", # J: 주식, ETF 등
        "FID_INPUT_ISCD": ticker_code  # 종목코드 (예: 005930)
    }

    try:
        # 2. 데이터 요청
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")

        data = response.json()
        
        # 응답 코드가 성공(0)이 아닐 경우 재시도
        if data['rt_cd'] != '0':
            print(f"Error msg: {data['msg1']}")
            return

        output = data['output']
        
        # 3. 데이터 파싱
        current_price = int(output['stck_prpr']) # 현재가
        volume = int(output['acml_vol'])         # 누적 거래량
        
        # -------------------------------------------------------
        # [Infra Strategy] Dual Write: Redis (Hot) + DB (Cold)
        # -------------------------------------------------------
        
        # A. Redis에 실시간 데이터 캐싱 (유효시간 60초)
        # 프론트엔드나 API 서버는 DB가 아닌 이 값을 읽어갑니다.
        redis_key = f"realtime_stock:{ticker_code}"
        redis_data = {
            "price": current_price,
            "volume": volume,
            "time": output['stck_cntg_hour'] # 체결 시간
        }
        cache.set(redis_key, redis_data, timeout=60)

        # B. DB에 영구 저장 (분석용)
        # *최적화 팁: 거래량이 변했을 때만 저장하거나, 
        # Bulk Insert를 위해 별도 큐로 넘기는 것이 좋으나 일단 직관적으로 저장합니다.
        StockPrice.objects.create(
            ticker=ticker_code,
            price=current_price,
            volume=volume
        )
        
        return f"Success: {ticker_code} - {current_price}"

    except Exception as e:
        # 실패 시 5초 뒤 재시도 (Celery 기능)
        raise self.retry(exc=e, countdown=5)