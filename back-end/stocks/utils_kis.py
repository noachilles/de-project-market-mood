import requests
import json
from django.conf import settings
from django.core.cache import cache

def get_kis_access_token():
    """
    한국투자증권 접근 토큰 발급 및 관리
    Redis 캐시를 활용하여 불필요한 재발급 방지
    """
    token_key = "kis_access_token"
    cached_token = cache.get(token_key)

    if cached_token:
        return cached_token

    url = f"{settings.KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": settings.KIS_APP_KEY,
        "appsecret": settings.KIS_APP_SECRET
    }

    res = requests.post(url, headers=headers, data=json.dumps(body))
    
    if res.status_code == 200:
        data = res.json()
        access_token = data['access_token']
        # 유효시간보다 약간 짧게 캐시 설정 (예: 23시간)
        cache.set(token_key, access_token, timeout=60*60*23) 
        return access_token
    else:
        raise Exception(f"Token 발급 실패: {res.text}")

def get_common_headers(tr_id):
    """
    API 호출에 필요한 공통 헤더 생성
    """
    token = get_kis_access_token()
    return {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": settings.KIS_APP_KEY,
        "appsecret": settings.KIS_APP_SECRET,
        "tr_id": tr_id, # Transaction ID (API 별로 다름)
        "custtype": "P", # 개인 설정
    }