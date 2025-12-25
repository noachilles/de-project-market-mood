# 웹소켓으로 받은 실시간 데이터가 연결된 결과를 확인할 수 있음

import asyncio
import websockets
import json
import datetime

async def listen_to_django():
    # 우리가 만든 Django 웹소켓 주소
    uri = "ws://localhost:8000/ws/stocks/"
    
    print(f"🔌 Django 서버({uri})에 접속 시도 중...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공! 데이터 대기 중... (Ctrl+C로 종료)")
            
            while True:
                # 1. Django가 보내주는 데이터를 기다림 (여기서 막히면 데이터가 안 넘어오는 것)
                message = await websocket.recv()
                
                # 2. 데이터 파싱
                data_json = json.loads(message)
                
                # 3. 출력 (이게 찍히면 성공!)
                current_time = datetime.datetime.now().strftime("%H:%M:%S")
                
                # 구조: {'type': 'stock_update', 'data': { ... }}
                real_data = data_json.get('data', {})
                code = real_data.get('code', 'UNKNOWN')
                price = real_data.get('price', 0)
                vol = real_data.get('volume', 0)
                
                print(f"[{current_time}] 📨 수신: {code} | 현재가: {price}원 | 거래량: {vol}")

    except ConnectionRefusedError:
        print("❌ 연결 실패: Django 서버가 꺼져있거나 포트(8000)가 다릅니다.")
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(listen_to_django())
    except KeyboardInterrupt:
        print("\n👋 테스트 종료")