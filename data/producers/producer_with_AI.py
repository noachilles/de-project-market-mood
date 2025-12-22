import time
import json
import os
import feedparser
import schedule
from kafka import KafkaProducer
from openai import OpenAI
from dotenv import load_dotenv
from utils.openai_client import get_openai_client
from datetime import datetime
from time import mktime

# --- 환경변수 로드 ---
load_dotenv()

KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "news_topic")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("ERROR: OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")


# --- RSS 소스 리스트 (Google + CNBC + 매일경제) ---
# 구글 뉴스는 'Technology'와 'Stock Market' 키워드로 검색된 RSS를 사용합니다.
RSS_SOURCES = [
    {
        "name": "Google_News", 
        "url": "https://news.google.com/rss/search?q=Technology+Stock+Market&hl=en-US&gl=US&ceid=US:en"
    },
    {
        "name": "CNBC_Tech", 
        "url": "https://www.cnbc.com/id/19854910/device/rss/rss.html"
    },
    {
        "name": "MK_Breaking", 
        "url": "https://www.mk.co.kr/rss/30000001/" # 매일경제 속보
    }
]

# --- 초기화 ---
client = get_openai_client()
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
sent_links = set() # 중복 방지 메모리

def normalize_date(entry):
    """
    어떤 RSS 날짜 형식이 와도 Flink가 좋아하는 ISO 8601 포맷으로 변환
    """
    try:
        # feedparser가 파싱해둔 시간 구조체(struct_time)를 사용
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            dt = datetime.fromtimestamp(mktime(entry.published_parsed))
            # ISO 8601 형식 문자열 반환 (예: 2025-12-11T10:00:00+09:00)
            # +00:00 (UTC) 기준으로 맞춥니다.
            return dt.strftime('%Y-%m-%dT%H:%M:%S+00:00')
    except Exception as e:
        print(f"Date Parsing Error: {e}")
    
    # 실패하면 현재 시간(UTC) 반환
    return datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')

def get_content(entry):
    """
    RSS마다 본문이 있는 태그가 다름 (content vs description vs summary)
    가장 긴 텍스트를 본문으로 채택
    """
    candidates = []
    
    # 1. content 태그 확인 (보통 전문이 여기 있음)
    if hasattr(entry, 'content'):
        for c in entry.content:
            candidates.append(c.value)
            
    # 2. description/summary 태그 확인
    if hasattr(entry, 'description'):
        candidates.append(entry.description)
    if hasattr(entry, 'summary'):
        candidates.append(entry.summary)
        
    # 후보 중 가장 긴 텍스트 선택 (짧은 건 단순 요약일 확률 높음)
    if candidates:
        return max(candidates, key=len)
    
    return "" # 본문 없음

def analyze_news_with_ai(title, description, source_name):
    """
    AI에게 뉴스 분석을 요청하는 핵심 함수
    """
    # 비용 절약을 위해 본문은 2000자로 제한
    # test를 통해서 어느정도 길이로 제한할 때 가장 좋은 성능과 정확도를 보이는지 확인
    truncated_content = description[:2000]

    prompt = f"""
    Analyze this news article provided by {source_name}.
    
    [Input Article]
    Title: {title}
    Content: {truncated_content}

    [Tasks]
    1. Summarize: Provide a 3-line summary in **Korean (Hangul)**.
    2. Sentiment: Determine if this is Positive/Negative/Neutral for the related stocks.
    3. Stock Mapping: Identify related companies in **US and South Korea**.
       - Format: "Region:Ticker" (e.g., US:AAPL, US:NVDA, KR:005930, KR:000660).
       - Important: If it's a US Tech news, find related Korean suppliers (e.g., Nvidia -> KR:000660).
    4. Keywords: Extract 3 English keywords.
    5. Reason: One short sentence in Korean explaining WHY these stocks are related.

    [Output Format (JSON Only)]
    {{
        "summary": "한글 요약 내용...",
        "sentiment": "Positive", 
        "keywords": "AI, Chip, Earnings",
        "symbols": ["US:NVDA", "KR:000660"],
        "reason": "엔비디아 칩 수요 증가는 하이닉스 HBM 매출에 긍정적"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a smart financial AI analyst. Output must be valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Error: {e}")
        # 에러 발생 시 빈 값 반환 (프로그램이 죽지 않도록)
        return {"summary": "요약 실패", "sentiment": "Neutral", "keywords": "", "symbols": [], "reason": ""}

def job():
    print(f"\n[{time.strftime('%H:%M:%S')}] 전체 RSS 소스 확인 시작...")
    
    for source in RSS_SOURCES:
        try:
            print(f" >> {source['name']} 읽는 중...")
            feed = feedparser.parse(source['url'])
            
            # 소스당 최신 5개만 확인 (너무 과거 데이터는 제외)
            for entry in feed.entries[:5]:
                if entry.link in sent_links:
                    continue
                
                print(f"    [New] {entry.title} ({source['name']})")
                
                safe_content = get_content(entry)
                safe_date = normalize_date(entry)   # 이제 모든 데이터가 ISO 포맷 가짐  

                # AI 분석 및 데이터
                ai_result = analyze_news_with_ai(entry.title, safe_content, source['name'])
                symbols_str = ",".join(ai_result.get('symbols', []))
                
                data = {
                    "title": entry.title,
                    "link": entry.link,
                    "content": safe_content[:5000], 
                    "published_at": safe_date,       # [중요] 정규화된 날짜
                    "source_name": source['name'],
                    "summary": ai_result.get('summary', '요약 없음'),
                    "sentiment": ai_result.get('sentiment', 'Neutral'),
                    "keywords": ai_result.get('keywords', ''),
                    "related_symbols": symbols_str,
                    "reason": ai_result.get('reason', '')
                }

                # 3. Kafka 전송
                producer.send(KAFKA_TOPIC, data)
                sent_links.add(entry.link)
                print(f"    -> 전송 완료! (감지된 종목: {symbols_str})")
                
                # API 부하 방지용 딜레이
                time.sleep(1) 
                
        except Exception as e:
            print(f"Error processing source {source['name']}: {e}")

    producer.flush()
    print("--- 이번 주기 수집 끝 (대기 중) ---")

# --- 실행 스케줄 (10분 주기) ---
# 즉, 10분마다 job 함수를 실행하라고 예약하는 코드
# RSS는 보통 10~30분 단위 업데이트가 적당함: 너무 빠르면 차단당함
schedule.every(10).minutes.do(job)

if __name__ == "__main__":
    job() # 시작 시 1회 즉시 실행

    # 자동화 시 아래 코드로 실행
    # while True:
        # schedule.run_pending()
        # time.sleep(1)