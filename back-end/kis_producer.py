import os
import sys
import json
import asyncio
import websockets
import django
from kafka import KafkaProducer
import requests

# ---------------------------------------------------------
# [Django 환경 설정 로드]
# ---------------------------------------------------------
# 1. 현재 경로를 시스템 경로에 추가 (모듈 import 문제 방지)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 2. Django 설정 모듈 지정 (프로젝트명.settings 로 수정 필수!)
# 예: 프로젝트 폴더명이 'config'라면 'config.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings") 

# 3. Django 초기화 (settings.py 로드)
django.setup()

# 4. settings import (django.setup() 이후에 해야 함)
from django.conf import settings
# ---------------------------------------------------------

# settings.py에서 가져온 변수 사용
APP_KEY = settings.KIS_APP_KEY
APP_SECRET = settings.KIS_APP_SECRET
# STOCK_CODE 등도 settings로 뺄 수 있지만, 편의상 여기 둠
STOCK_CODE = "005930" 

# Kafka 설정
KAFKA_BROKER = 'localhost:9092'
TOPIC_NAME = 'realtime-data'

def get_approval_key():
    url = "https://openapi.koreainvestment.com:9443/oauth2/Approval"
    headers = {"content-type": "application/json; utf-8"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": APP_SECRET
    }
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        res.raise_for_status()
        return res.json()["approval_key"]
    except Exception as e:
        print(f"Approval Key 발급 실패: {e}")
        sys.exit(1)

# Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

async def connect_kis_websocket():
    approval_key = get_approval_key()
    print(f"Approval Key 발급 완료: {approval_key[:10]}...")

    # 실전: ws://ops.koreainvestment.com:21000
    # 모의: ws://ops.koreainvestment.com:31000
    uri = "ws://ops.koreainvestment.com:21000"

    async with websockets.connect(uri, ping_interval=None) as websocket:
        print("KIS WebSocket Connected!")

        data = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0",
                    "tr_key": STOCK_CODE
                }
            }
        }
        await websocket.send(json.dumps(data))
        print(f"구독 요청 보냄: {STOCK_CODE}")

        while True:
            try:
                recv_data = await websocket.recv()
                
                # 데이터 전처리 및 전송
                if recv_data[0] in ['0', '1']:
                    # 실제 체결 데이터 파싱 로직은 필요에 따라 추가
                    # print(f"[KIS] {recv_data}") 
                    
                    msg_dict = {
                        "source": "KIS",
                        "code": STOCK_CODE,
                        "raw_data": recv_data
                    }
                    
                    producer.send(TOPIC_NAME, value=msg_dict)
                    producer.flush() # 즉시 전송
                    
            except websockets.exceptions.ConnectionClosed:
                print("연결 끊김, 재접속 필요")
                break
            except Exception as e:
                print(f"에러 발생: {e}")

if __name__ == "__main__":
    # 프로젝트명 수정 확인
    if os.environ.get("DJANGO_SETTINGS_MODULE") == "config.settings":
        print("⚠️ 주의: 'config.settings'가 실제 프로젝트명과 맞는지 확인하세요.")
        
    asyncio.run(connect_kis_websocket())