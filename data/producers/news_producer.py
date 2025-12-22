import os
import time
import json
import logging
import feedparser
from kafka import KafkaProducer
from datetime import datetime
from dateutil import parser as date_parser
from bs4 import BeautifulSoup  # HTML 태그 제거용 (구글 뉴스 등)

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kafka Producer 설정
BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092').split(',')

producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda x: json.dumps(x, ensure_ascii=False).encode('utf-8'),
    api_version=(0, 10, 1)
)

TOPIC_NAME = 'news-topic'

RSS_SOURCES = {
    'google': 'https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko',
    'mk': 'https://www.mk.co.kr/rss/30000001/',
    'khan': 'https://www.khan.co.kr/rss/rssdata/economy.xml'
}

seen_links = set()

def clean_html(html_text):
    """HTML 태그를 제거하고 순수 텍스트만 추출합니다."""
    if not html_text:
        return ""
    return BeautifulSoup(html_text, "html.parser").get_text(separator=" ", strip=True)

def normalize_news(entry, source_name):
    """
    각 언론사별 XML 특성을 반영하여 표준 데이터로 변환합니다.
    """
    # 1. 날짜 추출 (가장 중요)
    # feedparser가 1차적으로 'published'에 매핑하지만, 실패 시 원본 태그 확인
    raw_date = entry.get('published', '')
    
    # 경향신문은 <dc:date>를 사용하므로 feedparser가 'updated'로 매핑할 수 있음
    if not raw_date and 'updated' in entry:
        raw_date = entry.updated
        
    try:
        # dateutil이 GMT, +09:00, T 구분자 등을 자동으로 인식해서 datetime 객체로 변환
        dt = date_parser.parse(raw_date)
    except:
        logger.warning(f"날짜 파싱 실패: {raw_date} -> 현재 시간으로 대체")
        dt = datetime.now()

    # 2. 본문(Description) 추출 및 정제
    # 구글뉴스는 description에 <li> 태그가 잔뜩 들어있어서 HTML 제거 필요
    # 매일경제/경향신문은 CDATA 안에 텍스트가 있음 (feedparser가 자동 추출해줌)
    raw_summary = entry.get('summary', entry.get('description', ''))
    clean_summary = clean_html(raw_summary)

    # 3. 표준 스키마 반환
    return {
        "source": source_name,                          # 데이터 출처 (google, mk, khan)
        "title": entry.get('title', ''),                # 기사 제목
        "link": entry.get('link', ''),                  # 기사 원문 링크
        "summary": clean_summary[:1000],                # 본문 요약 (HTML 제거됨)
        "original_pub_date": raw_date,                  # 원본 날짜 문자열 (디버깅용)
        "published_at": dt.isoformat(),                 # 표준화된 날짜 (ISO 8601, Flink용)
        "collected_at": datetime.now().isoformat()      # 수집 시점
    }

def fetch_and_send():
    logger.info("뉴스 수집 사이클을 시작합니다...")
    
    for source_name, url in RSS_SOURCES.items():
        try:
            feed = feedparser.parse(url)
            logger.info(f"[{source_name}] 뉴스 {len(feed.entries)}개 감지")

            count = 0
            for entry in feed.entries:
                link = entry.get('link')
                
                if link in seen_links:
                    continue
                
                news_data = normalize_news(entry, source_name)
                
                # Kafka 전송
                producer.send(TOPIC_NAME, value=news_data)
                
                seen_links.add(link)
                count += 1
            
            logger.info(f" -> [{source_name}] 신규 뉴스 {count}건 전송 완료")
            
        except Exception as e:
            logger.error(f"[{source_name}] 에러 발생: {e}")

    producer.flush()

if __name__ == "__main__":
    while True:
        fetch_and_send()
        time.sleep(60)