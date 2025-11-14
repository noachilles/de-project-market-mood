import feedparser
import time
from kafka import KafkaProducer
import json

# (참고) docker-compose.yml에 설정한 Kafka의 외부 접속 포트(29092)
KAFKA_BROKER = 'localhost:29092'
KAFKA_TOPIC = 'news_articles'

# 주요 언론사 경제 RSS (예시)
RSS_URL = "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain"

def create_producer():
    """ Kafka Producer 인스턴스를 생성합니다. """
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        )
        print("Kafka Producer가 성공적으로 연결되었습니다.")
        return producer
    except Exception as e:
        print(f"Kafka 연결 오류: {e}")
        return None

# --- (신규) CSV 저장 함수 ---

def save_to_csv(news_data):
    """ 수집한 데이터를 CSV 파일에 누적 저장합니다. (Data Lake 역할) """
    
    # 1. 파일이 이미 존재하는지 확인 (헤더 중복 방지)
    file_exists = os.path.isfile(CSV_FILE)
    
    try:
        # 2. 'a' (append) 모드로 파일을 열어 데이터를 추가합니다.
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            # DictWriter를 사용하면 딕셔너리를 CSV로 쉽게 저장 가능
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            
            # 3. 파일이 새로 생성된 경우에만 헤더를 씁니다.
            if not file_exists:
                writer.writeheader()
                
            # 4. 데이터 한 행을 씁니다.
            writer.writerow(news_data)
            
    except Exception as e:
        print(f"CSV 저장 오류: {e}")

def fetch_and_send_rss(producer):
    """ RSS 피드를 파싱하고 Kafka로 전송합니다. """
    print(f"RSS 피드를 불러옵니다: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("새로운 뉴스가 없습니다.")
        return

    for entry in feed.entries:
        # 우리 프로젝트에 필요한 데이터만 추출
        news_data = {
            "title": entry.title,
            "link": entry.link,
            "published_at": entry.get('published_parsed', None), # 발행 시간
            "summary": entry.summary
        }
        
        # 1. Kafka로 데이터 전송
        try:
            producer.send(KAFKA_TOPIC, value=news_data)
            print(f"[Kafka 전송]: {entry.title[:30]}...")
        except Exception as e:
            print(f"Kafka 전송 오류: {e}")

        # 2. (추가) CSV 파일로 저장
        save_to_csv(news_data)
            
    # Kafka 프로듀서 버퍼에 남은 메시지를 모두 전송
    producer.flush()
    
if __name__ == "__main__":
    producer = create_producer()
    
    if producer:
        try:
            # 우선 1회 실행
            fetch_and_send_rss(producer)
            
            # (나중에는 Airflow가 이 스크립트를 주기적으로 실행)
            # while True:
            #     fetch_and_send_rss(producer)
            #     time.sleep(300) # 5분 대기
        except KeyboardInterrupt:
            print("프로듀서 종료.")
        finally:
            producer.close()