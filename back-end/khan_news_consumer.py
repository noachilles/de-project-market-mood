from kafka import KafkaConsumer
import json
import time

consumer = KafkaConsumer(
    'news_articles',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',  # 과거 메시지부터 읽기
    enable_auto_commit=False,
    group_id='heesoo-' + str(int(time.time())),  # 매번 새로운 그룹 ID
    value_deserializer=lambda v: json.loads(v.decode('utf-8'))
)

print("로딩중...")

for msg in consumer:
    print("\n===== NEW MESSAGE =====")
    print(json.dumps(msg.value, indent=2, ensure_ascii=False))
    print("=======================\n")
