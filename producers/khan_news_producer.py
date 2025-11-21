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

# --- 설정 ---
KAFKA_BROKER = 'kafka:9092'
KAFKA_TOPIC = 'news_articles'

RSS_URLS = {
    "경제": "https://www.khan.co.kr/rss/rssdata/economy_news.xml",
    "국제": "https://www.khan.co.kr/rss/rssdata/kh_world.xml",
}

BASE_DIR = "/home/ssafy/heesoo"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CSV_FILE = f'khan_news_{TIMESTAMP}.csv'
CSV_FIELDS = ['category', 'published_at', 'title', 'link', 'summary', 'content']

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

def scrape_article_content(url):
    try:
        time.sleep(random.uniform(1, 3))
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30])
        if not content:
            return "본문 수집 실패(구조 다름)"
        return content
    except Exception as e:
        print(f"⚠️ 본문 크롤링 실패 ({url}): {e}")
        return "본문 수집 실패(에러)"

def save_to_csv(news_data):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(news_data)

def fetch_enrich_send(producer):
    for category, rss_url in RSS_URLS.items():
        print(f"📡 [{category}] RSS 피드 확인 중: {rss_url}")
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            print(f"📭 [{category}] 새로운 뉴스 없음")
            continue

        print(f"[{category}] 총 {len(feed.entries)}개의 기사 발견. 크롤링 시작...")
        for entry in feed.entries:
            published_time = time.strftime('%Y-%m-%dT%H:%M:%SZ', entry.published_parsed) if entry.get('published_parsed') else None
            print(f"   Processing: {entry.title[:30]}...")
            full_content = scrape_article_content(entry.link)
            news_data = {
                "category": category,
                "published_at": published_time,
                "title": entry.title,
                "link": entry.link,
                "summary": getattr(entry, 'summary', ''),
                "content": full_content
            }
            producer.send(KAFKA_TOPIC, value=news_data)
            save_to_csv(news_data)
        producer.flush()
    print("✅ 모든 작업 완료.")

if __name__ == "__main__":
    producer = create_producer()
    if producer:
        fetch_enrich_send(producer)
        producer.close()
