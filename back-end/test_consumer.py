import os
import sys
import django
import json
import time
from kafka import KafkaConsumer

# ---------------------------------------------------------
# 1. Django 환경 수동 설정 (이게 핵심입니다!)
# ---------------------------------------------------------
# 현재 프로젝트의 settings 위치를 지정합니다. (프로젝트명.settings)
# 'back-end' 폴더 안의 프로젝트 폴더 이름을 확인하세요. 보통 'config' 또는 'project' 입니다.
# 만약 settings.py가 'config' 폴더 안에 있다면 'config.settings'로 적어야 합니다.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "marketmoodAPI.settings") # <-- 여기 수정 필요할 수 있음!

# Django 초기화 (이걸 해야 모델을 import 할 수 있습니다)
django.setup()

# ---------------------------------------------------------
# 2. 모델 Import (반드시 django.setup() 이후에 해야 함)
# ---------------------------------------------------------
from feeds.models import News

def run_consumer():
    print("🚀 [TEST] Kafka Consumer 시작 (Standalone Mode)")
    
    # Docker 내부에서 실행되므로 서비스 이름 'kafka' 사용
    KAFKA_BROKER = 'kafka:9092'
    TOPIC = 'news_articles'

    # 연결 시도
    try:
        consumer = KafkaConsumer(
            TOPIC,
            bootstrap_servers=[KAFKA_BROKER],
            group_id='test-group-01', # 테스트용 그룹 ID
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='earliest'
        )
        print("✅ Kafka 연결 성공!")
    except Exception as e:
        print(f"❌ Kafka 연결 실패: {e}")
        return

    print("📥 데이터 수신 대기 중... (Ctrl+C로 종료)")

    # 메시지 루프
    for message in consumer:
        data = message.value
        title = data.get('title')
        link = data.get('link')
        
        print(f"📨 수신: {title[:30]}...")

        try:
            # DB 저장 테스트
            obj, created = News.objects.update_or_create(
                link=link,
                defaults={
                    'title': title,
                    'summary': data.get('summary'),
                    'content': data.get('content'),
                    # 날짜는 형식 에러 날 수 있으니 일단 생략하거나 try-except 처리 권장
                    # 'published_at': data.get('published_at') 
                }
            )
            status = "🆕 생성됨" if created else "🔄 업데이트됨"
            print(f"   └─ DB 저장 완료: {status}")
            
        except Exception as e:
            print(f"   └─ 💥 DB 저장 에러: {e}")

if __name__ == "__main__":
    run_consumer()