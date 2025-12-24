import json
import logging
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import MapFunction, RuntimeContext
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer

# Redis 라이브러리는 런타임에 import (Flink TaskManager 안에 설치되어 있어야 함)
import redis

class RedisMapper(MapFunction):
    """
    Kafka 데이터를 받아서 Redis에 저장하고 Publish 하는 Mapper
    """
    def open(self, runtime_context: RuntimeContext):
        # TaskManager가 시작될 때 Redis 연결 (한 번만 연결)
        # docker-compose 서비스명 'redis' 사용
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        logging.info("Connected to Redis successfully.")

    def map(self, value):
        try:
            # 1. Kafka에서 받은 JSON 문자열 파싱
            data = json.loads(value)
            
            # 주식 코드 및 필요한 필드 추출
            # KIS API 파싱 로직에 따라 필드명이 다를 수 있으니 확인 필요
            # 앞선 Producer 코드 기준: '유가증권단축종목코드', '주식현재가', '주식체결시간' 등
            code = data.get('유가증권단축종목코드', 'UNKNOWN')
            price = data.get('주식현재가', '0')
            time_str = data.get('주식체결시간', '')
            
            # 2. [저장] Redis Hash에 최신 상태 저장 (API 조회용)
            # Key: "stock:current:{code}"
            redis_key = f"stock:current:{code}"
            self.redis_client.hset(redis_key, mapping={
                "price": price,
                "time": time_str,
                "raw": json.dumps(data) # 원본 데이터도 저장
            })
            
            # 3. [전파] Django가 구독할 채널로 Publish (WebSocket용)
            # Channel: "stock_updates"
            # Django가 이 채널을 구독하고 있다가 브라우저로 쏴줍니다.
            pub_message = json.dumps({
                "code": code,
                "price": price,
                "time": time_str,
                "full_data": data
            })
            self.redis_client.publish("stock_updates", pub_message)
            
            return f"Updated {code} -> {price}"
            
        except Exception as e:
            logging.error(f"Error processing data: {e}")
            return f"Error: {e}"

def main():
    # 1. Flink 실행 환경 설정
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1) # 순서 보장을 위해 1로 설정

    # 2. Kafka Source 설정
    properties = {
        'bootstrap.servers': 'kafka:9092', # Docker 내부 주소
        'group.id': 'flink-stock-group',
        'auto.offset.reset': 'latest' # 가장 최신 데이터부터 읽기
    }

    kafka_consumer = FlinkKafkaConsumer(
        topics='stock-ticks', # Producer가 쏘는 토픽 이름
        deserialization_schema=SimpleStringSchema(),
        properties=properties
    )

    # 3. 데이터 흐름 정의: Source -> Map(Redis) -> Print(Log)
    ds = env.add_source(kafka_consumer)
    
    # RedisMapper를 통해 데이터 처리
    ds.map(RedisMapper()).print() # .print()는 TaskManager 로그에 출력됨

    # 4. Job 실행
    env.execute("Stock Real-time Redis ETL")

if __name__ == '__main__':
    main()