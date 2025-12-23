import json
from kafka import KafkaConsumer
import redis
import psycopg2
from datetime import datetime
import os

# =====================
# Kafka
# =====================
consumer = KafkaConsumer(
    "stock-ticks",
    bootstrap_servers=["kafka:9092"],
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="latest",
    enable_auto_commit=True,
    group_id="stock-consumer-group",
)

# =====================
# Redis
# =====================
redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)

# # =====================
# # Postgres
# # =====================
# pg_conn = psycopg2.connect(
#     host="postgres",
#     port=5432,
#     dbname=os.getenv("POSTGRES_DB"),
#     user=os.getenv("POSTGRES_USER"),
#     password=os.getenv("POSTGRES_PASSWORD"),
# )
# pg_cur = pg_conn.cursor()

print("🚀 Stock Consumer started")

for msg in consumer:
    try:
        data = msg.value

        # ✅ [수정 1] 한글 키값 매핑 (Producer가 보낸 이름으로 꺼내야 함)
        # ---------------------------------------------------------
        code = data.get("유가증권단축종목코드")   # data["code"] (X) -> data.get("유가증권...") (O)
        price = data.get("주식현재가")          # data["price"] (X)
        volume = data.get("체결거래량")         # data["volume"] (X)
        change_rate = data.get("전일대비율", 0)  # data["change_rate"] (X)
        
        # 타임스탬프 처리 (Producer는 'ingest_time'으로 보냄)
        ts_str = data.get("ingest_time")       # data["timestamp"] (X)
        
        # 데이터가 없으면 건너뛰기 (유효성 검사)
        if not code or not price:
            continue

        # ✅ [수정 2] 데이터 형변환 (String -> Int/Float)
        # KIS 데이터는 문자열로 오므로 숫자로 바꿔줘야 함
        try:
            price = int(price)
            volume = int(volume)
            change_rate = float(change_rate)
        except ValueError:
            pass # 변환 실패 시 원본 문자열 유지

        # ✅ [수정 3] 타임스탬프 형식 통일
        if ts_str:
            ts = datetime.fromisoformat(ts_str) # 문자열 -> datetime 객체
        else:
            ts = datetime.now() # 없으면 현재시간

        # ---------------------------------------------------------

        # 1️⃣ Redis (현재가 저장)
        redis_key = f"current_price:{code}"
        redis_client.set(redis_key, json.dumps({
            "code": code,
            "price": price,
            "change_rate": change_rate,
            "volume": volume,
            "timestamp": str(ts)
        }))

        # 2️⃣ Redis Pub/Sub (Django에게 실시간 전파)
        # Django는 영어 키값(code, price...)을 기대하므로 여기서 변환해서 쏴줍니다.
        redis_client.publish("stock_updates", json.dumps({
            "code": code,
            "price": price,
            "volume": volume,
            "change_rate": change_rate,
            "timestamp": str(ts)
        }))
        
        # 3️⃣ Postgres (주석 처리됨 - 유지)
        # ...

        print(f"📈 {code} | {price} | {volume}")

    except Exception as e:
        print("❌ Consumer Error:", e)
        # 어떤 데이터 때문에 에러 났는지 확인용 로그
        # print(f"   -> Problem Data Keys: {data.keys()}")