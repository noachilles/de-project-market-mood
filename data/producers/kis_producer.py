import websockets
import json
import os
import asyncio
import requests
import datetime
from kafka import KafkaProducer

# ==========================================
# 1. 환경 설정 (한국투자증권 & Kafka)
# ==========================================
# .env 파일이나 Docker env로 주입받아야 합니다.
APP_KEY = os.getenv("KIS_APP_KEY", "여기에_APP_KEY_입력")
APP_SECRET = os.getenv("KIS_APP_SECRET", "여기에_APP_SECRET_입력")

# KAFKA 설정
KAFKA_BROKER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TOPIC_NAME = "stock-ticks"

# KIS API URL (실전투자 기준)
# 모의투자인 경우: https://openapivts.koreainvestment.com:29443
REST_BASE_URL = "https://openapi.koreainvestment.com:9443"
WS_BASE_URL = "ws://ops.koreainvestment.com:21000"

# 구독할 종목 코드 (예: 삼성전자 005930)
TARGET_CODE = "005930"

# ==========================================
# 2. Kafka Producer 초기화
# ==========================================
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    api_version=(0, 10, 1)
)

# ==========================================
# 3. 데이터 파싱 로직 (제공해주신 코드 통합)
# ==========================================
def parse_and_send(data_cnt, data):
    """
    KIS에서 받은 Raw String을 파싱하여 JSON으로 변환 후 Kafka로 전송
    """
    # 제공해주신 필드 명세
    menulist = "유가증권단축종목코드|주식체결시간|주식현재가|전일대비부호|전일대비|전일대비율|가중평균주식가격|주식시가|주식최고가|주식최저가|매도호가1|매수호가1|체결거래량|누적거래량|누적거래대금|매도체결건수|매수체결건수|순매수체결건수|체결강도|총매도수량|총매수수량|체결구분|매수비율|전일거래량대비등락율|시가시간|시가대비구분|시가대비|최고가시간|고가대비구분|고가대비|최저가시간|저가대비구분|저가대비|영업일자|신장운영구분코드|거래정지여부|매도호가잔량|매수호가잔량|총매도호가잔량|총매수호가잔량|거래량회전율|전일동시간누적거래량|전일동시간누적거래량비율|시간구분코드|임의종료구분코드|정적VI발동기준가"
    keys = menulist.split('|')
    
    # 데이터는 '^'로 구분됨
    values = data.split('^')
    
    # 데이터 개수 검증
    if len(values) < len(keys):
        # 가끔 마지막에 더미 데이터가 붙거나 형식이 다를 수 있음
        print(f"[Warning] Data length mismatch. Expected {len(keys)}, Got {len(values)}")
        return

    # 1. Dictionary 변환 (JSON 구조화)
    # zip을 사용하여 키-값 쌍으로 묶음
    stock_data = dict(zip(keys, values))
    
    # 2. 데이터 타입 보정 (필요시)
    # 예: 가격이나 거래량은 문자열 -> 정수로 변환해야 시각화때 편함
    try:
        stock_data['주식현재가'] = int(stock_data['주식현재가'])
        stock_data['체결거래량'] = int(stock_data['체결거래량'])
    except:
        pass # 변환 실패시 그냥 문자열로 전송

    # 3. 타임스탬프 추가 (데이터 발생 시각)
    stock_data['ingest_time'] = str(datetime.datetime.now())

    # 4. Kafka 전송
    producer.send(TOPIC_NAME, value=stock_data)
    producer.flush() # 즉시 전송 강제
    
    # 로그 출력 (확인용)
    print(f"✅ [Kafka Sent] {stock_data['주식체결시간']} | {stock_data['주식현재가']}원 | Vol: {stock_data['체결거래량']}")


# ==========================================
# 4. 인증키 발급 (REST API)
# ==========================================
def get_approval_key(key, secret):
    url = f"{REST_BASE_URL}/oauth2/Approval"
    headers = {"content-type": "application/json; utf-8"}
    body = {"grant_type": "client_credentials", "appkey": key, "secretkey": secret}
    
    try:
        res = requests.post(url, headers=headers, data=json.dumps(body))
        res.raise_for_status()
        return res.json()["approval_key"]
    except Exception as e:
        print(f"⛔ 인증키 발급 실패: {e}")
        # 실패 시 프로그램 종료 (키 없으면 접속 불가)
        raise

# ==========================================
# 5. 웹소켓 메인 로직
# ==========================================
async def connect_to_kis():
    # 1. 접속키 발급
    print("🔑 승인키 발급 요청 중...")
    approval_key = get_approval_key(APP_KEY, APP_SECRET)
    print(f"🔑 승인키 획득 완료: {approval_key[:10]}...")

    # 2. 웹소켓 연결
    async with websockets.connect(f"{WS_BASE_URL}/tryitout/H0STCNT0", ping_interval=60) as websocket:
        print(f"🌐 한국투자증권 WebSocket 연결 성공 ({WS_BASE_URL})")

        # 3. 구독 요청 패킷 생성
        # 국내주식 실시간 체결가 (TR_ID: H0STCNT0)
        request_body = {
            "header": {
                "approval_key": approval_key,
                "custtype": "P",
                "tr_type": "1", # 1: 등록(구독), 2: 해제
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "H0STCNT0", 
                    "tr_key": TARGET_CODE 
                }
            }
        }
        
        # 구독 요청 전송
        await websocket.send(json.dumps(request_body))
        print(f"📡 종목 [{TARGET_CODE}] 구독 요청 전송 완료")

        # 4. 데이터 수신 루프
        while True:
            try:
                recv_data = await websocket.recv()
                
                # 수신 데이터 첫 글자로 데이터 타입 구분
                # '0': 실시간 데이터 (평문)
                # '1': 실시간 데이터 (암호화) - 국내주식은 보통 평문으로 옴
                
                if recv_data[0] == '0':
                    # 형식: 0|TR_ID|데이터개수|데이터(^)
                    parts = recv_data.split('|')
                    if len(parts) >= 4:
                        data_cnt = int(parts[2]) # 데이터 개수
                        raw_data = parts[3]      # 실제 데이터 (A^B^C...)
                        
                        # 파싱 및 Kafka 전송 함수 호출
                        parse_and_send(data_cnt, raw_data)
                        
                elif recv_data[0] == '1':
                    print("⚠️ 암호화된 데이터가 수신되었습니다. (현재 로직은 평문만 처리)")
                    # 필요 시 AES 복호화 로직 추가 (user imports 활용)
                    
                else:
                    # PINGPONG 또는 시스템 메시지
                    try:
                        msg_json = json.loads(recv_data)
                        print(f"ℹ️ 시스템 메시지: {msg_json.get('header', {}).get('tr_id')}")
                    except:
                        print(f"ℹ️ 기타 메시지: {recv_data}")

            except websockets.ConnectionClosed:
                print("❌ 연결이 종료되었습니다. 재연결을 시도합니다...")
                break
            except Exception as e:
                print(f"❌ 에러 발생: {e}")
                # 에러 발생 시 잠시 대기
                await asyncio.sleep(1)

if __name__ == "__main__":
    # 윈도우 환경인 경우 asyncio 정책 설정 필요할 수 있음
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_to_kis())