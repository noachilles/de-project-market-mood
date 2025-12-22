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
    "stock.realtime",
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

# =====================
# Postgres
# =====================
pg_conn = psycopg2.connect(
    host="postgres",
    port=5432,
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)
pg_cur = pg_conn.cursor()

print("🚀 Stock Consumer started")

for msg in consumer:
    try:
        data = msg.value

        code = data["code"]
        price = data["price"]
        volume = data["volume"]
        change_rate = data.get("change_rate", 0)
        ts = datetime.fromisoformat(data["timestamp"])

        # 1️⃣ Redis (현재가)
        redis_key = f"current_price:{code}"
        redis_client.set(redis_key, json.dumps({
            "price": price,
            "change_rate": change_rate,
            "volume": volume,
            "timestamp": data["timestamp"]
        }))

        # 2️⃣ Postgres (차트)
        pg_cur.execute("""
            INSERT INTO stock_prices (code, ts, price, volume)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (code, ts, price, volume))
        pg_conn.commit()

        print(f"📈 {code} | {price} | {volume}")

    except Exception as e:
        print("❌ Consumer Error:", e)
        pg_conn.rollback()
