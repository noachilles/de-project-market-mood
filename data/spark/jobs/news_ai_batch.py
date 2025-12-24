# /app/jobs/news_ai_batch.py
import os
import json
import time
from typing import Iterator, List, Dict, Any, Tuple

import requests
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, from_utc_timestamp, to_timestamp

# .env 로드
load_dotenv()

# --- 환경 변수 설정 ---
# Worker 노드에서도 접근 가능하도록 함수 내부에서 다시 로드할 준비
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://gms.ssafy.io/gmsapi/api.openai.com/v1")

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_USER = os.getenv("POSTGRES_USER", "ssafyuser")
DB_PWD = os.getenv("POSTGRES_PASSWORD", "ssafy")

SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")
BATCH_SIZE = int(os.getenv("AI_BATCH_SIZE", "16"))
MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "5"))


def _headers() -> Dict[str, str]:
    # Worker 내부 유실 방지를 위해 os.environ에서 직접 조회
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv("/app/.env")
        api_key = os.environ.get("OPENAI_API_KEY")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _retry_post(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            r = requests.post(url, headers=_headers(), json=payload, timeout=60)
            if r.status_code >= 200 and r.status_code < 300:
                return r.json()
            time.sleep(min(2 ** i, 10))
        except Exception as e:
            last_err = e
            time.sleep(min(2 ** i, 10))
    raise RuntimeError(f"OpenAI request failed: {last_err}")

# --- AI 및 저장 로직 ---
def openai_summarize_stock_total(ticker: str, combined_content: str) -> Tuple[str, float]:
    system_instruction = (
        f"You are a senior investment strategist. Analyze news for ticker: {ticker}. "
        "Summarize the overall flow into EXACTLY 2 Korean sentences. "
        "Return JSON: { 'summary': '...', 'sentiment_score': float }"
    )
    payload = {
        "model": SUMMARY_MODEL,
        "messages": [{"role": "system", "content": system_instruction}, {"role": "user", "content": combined_content}],
        "response_format": {"type": "json_object"},
        "temperature": 0.3,
    }
    try:
        data = _retry_post(f"{OPENAI_BASE_URL}/chat/completions", payload)
        obj = json.loads(data['choices'][0]['message']['content'])
        return obj.get("summary", ""), float(obj.get("sentiment_score", 0.0))
    except Exception as e:
        print(f"❌ AI Error for {ticker}: {e}")
        return "", 0.0

def save_stock_daily_report(ticker: str, summary: str, score: float, target_date: str) -> None:
    if not summary: return
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
        cur = conn.cursor()
        # CURRENT_DATE 대신 target_date를 직접 전달하여 정확한 날짜에 저장
        cur.execute("""
            INSERT INTO stocks_stockdailyreport (stock_id, ai_summary, sentiment_avg, target_date)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (stock_id, target_date) 
            DO UPDATE SET ai_summary = EXCLUDED.ai_summary, sentiment_avg = EXCLUDED.sentiment_avg;
        """, (ticker, summary, score, target_date))
        conn.commit()
        print(f"✅ Saved report for {ticker} on {target_date}")
    except Exception as e:
        print(f"❌ DB Error for {ticker}: {e}")
    finally:
        if conn: conn.close()

# --- Partition 처리 ---
def _flush_batch(payload_rows: List[Row], target_date: str) -> int:
    SAMSUNG_CODE = "005930"  # 테스트용 타겟 코드
    samsung_news_contents = []
    rows_as_dict = [r.asDict() for r in payload_rows]

    for r in rows_as_dict:
        t = r.get("title", "")
        c = (r.get("content") or r.get("body") or "")[:500]
        codes = r.get("related_stocks") or r.get("stock_codes") or []
        
        # 삼성전자 코드가 포함된 뉴스만 수집
        if SAMSUNG_CODE in codes:
            samsung_news_contents.append(f"제목: {t}\n내용: {c}")

    if not samsung_news_contents:
        return 0

    # 1. 삼성전자 관련 뉴스들을 하나로 합침 (최대 10개)
    combined_text = "\n---\n".join(samsung_news_contents[:10])
    
    # 2. AI 요약 및 감성 분석 수행
    print(f"🤖 삼성전자 관련 뉴스 {len(samsung_news_contents)}건 분석 중...")
    summary, score = openai_summarize_stock_total(SAMSUNG_CODE, combined_text)
    
    # 3. DB 저장
    if summary:
        save_stock_daily_report(SAMSUNG_CODE, summary, score, target_date)
        print(f"✨ [SAMSUNG] {target_date} 리포트 저장 완료!")
        return 1
    
    return 0

def process_partition(rows: Iterator[Row], target_date: str) -> Iterator[int]:
    # 삼성전자는 데이터 양이 적을 수 있으므로 파티션 전체를 모아서 한 번에 처리
    batch = list(rows)
    if batch:
        yield _flush_batch(batch, target_date)
    else:
        yield 0

def main():
    spark = SparkSession.builder.appName("news-ai-batch-samsung").getOrCreate()
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    
    path = f"/opt/data-lake/news_enriched/dt={target_date}"
    if not os.path.exists(path):
        print(f"❌ '{target_date}' 데이터를 찾을 수 없습니다.")
        return

    try:
        df = spark.read.parquet(path)
        
        # RDD로 변환하여 삼성전자 전용 로직 수행
        final_counts = df.rdd.mapPartitions(lambda rows: process_partition(rows, target_date)).collect()
        
        total_reports = sum(final_counts)
        if total_reports > 0:
            print(f"✅ [DONE] 삼성전자 리포트 생성 성공!")
        else:
            print(f"⚠️ 해당 날짜({target_date}) 뉴스 중 삼성전자 관련 내용이 없습니다.")
            
    finally:
        spark.stop()

if __name__ == "__main__":
    main()
