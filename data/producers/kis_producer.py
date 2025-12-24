import websockets
import json
import os
import asyncio
import requests
import datetime
import random
import sys
from kafka import KafkaProducer

# ==========================================
# 1. 환경 설정
# ==========================================
APP_KEY = os.getenv("KIS_APP_KEY", "여기에_APP_KEY_입력")
APP_SECRET = os.getenv("KIS_APP_SECRET", "여기에_APP_SECRET_입력")
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "stock-ticks"

REST_BASE_URL = "https://openapi.koreainvestment.com:9443"
WS_BASE_URL = "ws://ops.koreainvestment.com:21000"
TARGET_CODE = "005930"

# Kafka Producer 초기화
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    api_version=(0, 10, 1)
)

# 필드 명세 (공통 사용)
MENULIST = "유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|시간구분코드|임의종료구분코드|정적VI발동기준가"

# ==========================================
# 2. 데이터 처리 및 전송 로직
# ==========================================
def parse_and_send(data):
    keys = MENULIST.split('|')
    values = data.split('^')
    
    if len(values) < len(keys):
        print(f"[Warning] Data mismatch. Expected {len(keys)}, Got {len(values)}")
        return

    stock_data = dict(zip(keys, values))
    
    try:
        stock_data['주식현재가'] = int(stock_data['주식현재가'])
        stock_data['체결거래량'] = int(stock_data['체결거래량'])
    except:
        pass

    stock_data['ingest_time'] = str(datetime.datetime.now())
    producer.send(TOPIC_NAME, value=stock_data)
    producer.flush()
    print(f"✅ [Kafka Sent] {stock_data['주식체결시간']} | {stock_data['주식현재가']}원 | Vol: {stock_data['체결거래량']}")

# ==========================================
# 3. 밤시간 테스트용 Mock Data 생성기
# ==========================================
async def run_mock_producer():
    """장이 닫혔을 때 가짜 데이터를 생성하여 Kafka로 전송"""
    print("🛠 [Test Mode] 가짜 데이터를 생성 중입니다... (Ctrl+C로 종료)")
    while True:
        now_str = datetime.datetime.now().strftime("%H%M%S")
        # 가짜 데이터를 '^' 구분자로 생성
        mock_values = [TARGET_CODE, now_str, str(random.randint(70000, 75000))] + ["0"] * (len(MENULIST.split('|')) - 3)
        mock_raw_data = "^".join(mock_values)
        
        parse_and_send(mock_raw_data)
        await asyncio.sleep(1) # 1초 간격 전송

# ==========================================
# 4. KIS 실시간 API 로직
# ==========================================
def get_approval_key(key, secret):
    url = f"{REST_BASE_URL}/oauth2/Approval"
    headers = {"content-type": "application/json; utf-8"}
    body = {"grant_type": "client_credentials", "appkey": key, "secretkey": secret}
    res = requests.post(url, headers=headers, data=json.dumps(body))
    res.raise_for_status()
    return res.json()["approval_key"]

async def connect_to_kis():
    print("🔑 승인키 발급 요청 중...")
    try:
        approval_key = get_approval_key(APP_KEY, APP_SECRET)
    except Exception as e:
        print(f"⛔ 인증 실패: {e}\n💡 장 마감 후라면 'python kis_producer.py test'를 실행하세요.")
        return

    async with websockets.connect(f"{WS_BASE_URL}/tryitout/H0STCNT0", ping_interval=60) as websocket:
        request_body = {
            "header": {"approval_key": approval_key, "custtype": "P", "tr_type": "1", "content-type": "utf-8"},
            "body": {"input": {"tr_id": "H0STCNT0", "tr_key": TARGET_CODE}}
        }
        await websocket.send(json.dumps(request_body))
        
        while True:
            try:
                recv_data = await websocket.recv()
                if recv_data[0] == '0':
                    parts = recv_data.split('|')
                    if len(parts) >= 4:
                        parse_and_send(parts[3])
                elif recv_data[0] == '1':
                    print("⚠️ 암호화 데이터 수신 (미처리)")
                else:
                    print(f"ℹ️ 메시지: {recv_data}")
            except websockets.ConnectionClosed:
                print("❌ 연결 종료. 재시도 중...")
                break

# ==========================================
# 5. 메인 실행 제어
# ==========================================
if __name__ == "__main__":
    # 실행 인자 확인 (test 인자가 있으면 Mock 모드로 실행)
    mode = sys.argv[1] if len(sys.argv) > 1 else "real"
    
    loop = asyncio.get_event_loop()
    if mode == "test":
        loop.run_until_complete(run_mock_producer())
    else:
        loop.run_until_complete(connect_to_kis())