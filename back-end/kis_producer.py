# producer.py (최종 자동화 버전)
import websockets
import json
import os
import asyncio
import time
import requests # requests 라이브러리 필요
from kafka import KafkaProducer
from dotenv import load_dotenv

# 1. 환경변수 로드
load_dotenv()

# .env에 있는 기본 키 가져오기
APP_KEY = os.getenv("KIS_APP_KEY")
APP_SECRET = os.getenv("KIS_APP_SECRET")

# Kafka 설정
KAFKA_BOOTSTRAP_SERVERS = ['kafka:9092']
KAFKA_TOPIC = 'stock_updates'

# -----------------------------------------------------------
# 2. 웹소켓 접속키(Approval Key) 자동 발급 함수
# -----------------------------------------------------------
def get_approval_key(key, secret):
    # 모의투자 URL
    url = "https://openapivts.koreainvestment.com:29443/oauth2/Approval"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": key,
        "secretkey": secret
    }
    
    print("🔑 웹소켓 접속키 발급 요청 중...")
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        if res.status_code == 200:
            return res.json()["approval_key"]
        else:
            raise Exception(f"발급 실패: {res.text}")
    except Exception as e:
        print(f"❌ 키 발급 중 에러 발생: {e}")
        exit(1)

# -----------------------------------------------------------
# 3. 메인 로직
# -----------------------------------------------------------
async def connect():
    # [자동 발급] 실행할 때마다 새로운 키를 받아옵니다.
    APPROVAL_KEY = get_approval_key(APP_KEY, APP_SECRET)
    print(f"✅ 접속키 확보 완료: {APPROVAL_KEY[:10]}...")

    # Kafka 연결 (재시도 로직)
    producer = None
    for i in range(10):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                acks=0
            )
            print("✅ Kafka Connected!")
            break
        except:
            print(f"⏳ Kafka 연결 대기 중... ({i+1}/10)")
            time.sleep(3)
    
    if not producer:
        print("❌ Kafka 연결 실패")
        return

    # 웹소켓 접속
    uri = "ws://ops.koreainvestment.com:31000"

    async with websockets.connect(uri, ping_interval=None) as websocket:
        print("✅ WebSocket Connected to KIS!")

        # 구독 요청
        send_data = {
            "header": {
                "approval_key": APPROVAL_KEY, # 자동 발급된 키 사용
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            # 한국장 주식 (9:00 ~ 15:30)
            # "body": {
            #     "input": {
            #         "tr_id": "H0STCNT0",
            #         "tr_key": "005930" 
            #     }
            # }
            
            # 미국장 주식 (18:00 ~)
            "body": {
                "input": {
                "tr_id": "HDFSCNT0",   # 해외주식 실시간 체결가 ID
                "tr_key": "DNASTSLA"   # D(구분) + NAS(나스닥) + TSLA(티커)
                }
            }
        }

        # 공백 제거 필수
        await websocket.send(json.dumps(send_data, separators=(',', ':'), ensure_ascii=False))
        print("📨 구독 요청 전송 완료")

        while True:
            try:
                recv_data = await websocket.recv()
                
                # ** PINGPONG 처리 (가장 중요) - 데이터 전송 확인
                if 'PINGPONG' in recv_data:
                    # PONG으로 답장 보내기 (데이터 그대로 다시 전송)
                    await websocket.send(recv_data)
                    print(f"🏓 PONG Sent! (Connection Alive)")
                    continue # 다음 루프로

                if recv_data[0] in ['0', '1']:
                    # 실시간 데이터 처리
                    splitted = recv_data.split('|')
                    if len(splitted) > 3:
                        raw_data = splitted[3]
                        producer.send(KAFKA_TOPIC, value={'message': raw_data})
                        print(f"🚀 Data Sent: {raw_data[:20]}...")
                else:
                    # 시스템 메시지 (PINGPONG 등)
                    print(f"🔔 System: {recv_data}")

            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(connect())