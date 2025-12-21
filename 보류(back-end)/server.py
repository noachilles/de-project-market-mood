import asyncio
import json
import websockets
from kafka import KafkaConsumer

# 1. Kafka 설정 (Docker 내부 통신용 주소 사용)
KAFKA_BROKER = 'kafka:29092' 
TOPIC_NAME = 'realtime-data'

async def send_kafka_data(websocket):
    print("New Client Connected!")
    # Kafka Consumer 생성
    consumer = KafkaConsumer(
        TOPIC_NAME,
        bootstrap_servers=[KAFKA_BROKER],
        auto_offset_reset='latest', # 가장 최신 데이터부터 읽기
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    try:
        # Kafka 메시지가 오면 바로 웹소켓으로 쏘기
        for message in consumer:
            data = message.value
            print(f"Sending: {data}")
            await websocket.send(json.dumps(data))
            await asyncio.sleep(0) # 다른 작업 양보
    except Exception as e:
        print(f"Error: {e}")
    finally:
        consumer.close()

async def main():
    # 웹소켓 서버 시작 (8765 포트)
    async with websockets.serve(send_kafka_data, "0.0.0.0", 8765):
        print("WebSocket Server Started on port 8765...")
        await asyncio.Future()  # 영원히 실행

if __name__ == "__main__":
    asyncio.run(main())