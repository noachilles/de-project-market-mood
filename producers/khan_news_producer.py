import feedparser
import requests
from bs4 import BeautifulSoup
import time
import random
import json
import csv
import os
from kafka import KafkaProducer
from datetime import datetime
import dateutil.parser # pip install python-dateutil 필수

# --- 설정 ---
KAFKA_BROKER = 'kafka:9092'
KAFKA_TOPIC = 'news_articles'

RSS_URLS = {
    "경제": "https://www.khan.co.kr/rss/rssdata/economy_news.xml",
    "국제": "https://www.khan.co.kr/rss/rssdata/kh_world.xml",
}

STATE_FILE = "producer_state.json"
CSV_FILE = f'khan_news_{datetime.now().strftime("%Y%m%d")}.csv'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def create_producer():
    try:
        producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            api_version=(0, 10, 1),
            value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8')
        )
        print("✅ Kafka Producer 연결 성공")
        return producer
    except Exception as e:
        print(f"❌ Kafka 연결 실패: {e}")
        return None

# --- [핵심 1] 상태 관리 함수 ---
def load_last_published_at():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_last_published_at(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

# --- [핵심 2] 날짜 처리 헬퍼 ---
def parse_date(date_str):
    """RSS 날짜 문자열 -> datetime 객체 변환"""
    try:
        return dateutil.parser.parse(date_str)
    except:
        return datetime.now()

def get_safe_date(entry):
    """
    entry에서 날짜를 안전하게 추출합니다.
    published가 없으면 updated, date, dc_date 순서로 찾습니다.
    """
    return (entry.get('published') or 
            entry.get('updated') or 
            entry.get('date') or 
            entry.get('dc_date') or 
            "1970-01-01T00:00:00+00:00")

def scrape_article_content(url):
    try:
        time.sleep(random.uniform(0.5, 1.5))
        response = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 본문 영역 찾기 (ID 우선, Class 차선)
        article_body = soup.find(id="articleBody") or soup.find(attrs={"class": "art_body"})
        
        if article_body:
            paragraphs = article_body.find_all('p')
            content = ' '.join([p.get_text().strip() for p in paragraphs])
            return content if content else ""
        return ""
    except Exception as e:
        print(f"   ⚠️ 본문 수집 실패: {e}")
        return ""

def fetch_enrich_send(producer):
    # 1. 상태 로드 (마지막 수집 시간)
    state = load_last_published_at()
    
    for category, rss_url in RSS_URLS.items():
        print(f"\n📡 [{category}] RSS 확인 중...")
        
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            continue

        # 2. 마지막 수집 시간 확인
        last_seen_str = state.get(category, "2000-01-01T00:00:00+00:00")
        last_seen_dt = parse_date(last_seen_str)
        
        new_entries = []
        
        # 3. 새로운 뉴스 필터링
        for entry in feed.entries:
            # [수정] 헬퍼 함수를 통해 안전하게 날짜 문자열 획득
            entry_date_str = get_safe_date(entry)
            entry_dt = parse_date(entry_date_str)
            
            # 이미 본 뉴스(과거 시간)라면 중단
            if entry_dt <= last_seen_dt:
                break
                
            new_entries.append(entry)

        if not new_entries:
            print(f"   ✅ 새로운 기사가 없습니다. (Last: {last_seen_str})")
            continue

        print(f"   🚀 {len(new_entries)}개의 **새로운** 기사 발견! 수집 시작...")
        
        # 이번 배치의 가장 최신 날짜 저장 (다음번 비교 기준이 됨)
        latest_date_in_batch = get_safe_date(new_entries[0])

        for entry in new_entries:
            # [수정] 안전한 날짜 사용
            date_str = get_safe_date(entry)
            
            # [여기가 수정됨!] entry.published 대신 date_str 사용
            print(f"   Processing: {entry.title[:20]}... ({date_str})")
            
            full_content = scrape_article_content(entry.link)
            
            news_data = {
                "category": category,
                "published_at": date_str, # 안전한 날짜 저장
                "title": entry.title,
                "link": entry.link,
                "summary": getattr(entry, 'summary', ''),
                "content": full_content,
                "feed_last_build_date": latest_date_in_batch
            }
            
            # Kafka 전송
            producer.send(KAFKA_TOPIC, value=news_data)
            
            # CSV 저장
            with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=news_data.keys())
                if f.tell() == 0: writer.writeheader()
                writer.writerow(news_data)

        # 4. 상태 업데이트
        state[category] = latest_date_in_batch
        save_last_published_at(state)
        producer.flush()

    print("\n✅ 사이클 완료.")

if __name__ == "__main__":
    producer = create_producer()
    if producer:
        fetch_enrich_send(producer)
        producer.close()