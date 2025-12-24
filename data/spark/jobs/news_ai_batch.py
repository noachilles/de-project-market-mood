import sys
import os
import json
import time
import requests
import psycopg2
from typing import Iterator, List, Dict, Any, Tuple
from dotenv import load_dotenv
from datetime import datetime, timedelta

from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import col, from_utc_timestamp, to_timestamp

# .env 로드
load_dotenv()

# --- 환경 변수 설정 ---
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://gms.ssafy.io/gmsapi/api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

ES_BASE_URL = os.getenv("ES_BASE_URL", "http://elasticsearch:9200")
ES_INDEX = os.getenv("ES_INDEX", "news-ai-vector")

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "joo_db")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PWD = os.getenv("POSTGRES_PASSWORD", "password")

EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMS = int(os.getenv("EMBED_DIMS", "512"))
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-4o-mini")

BATCH_SIZE = int(os.getenv("AI_BATCH_SIZE", "16"))
MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "5"))

# --- 유틸리티 함수 ---
def _headers() -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is empty.")
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

def _retry_post(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            r = requests.post(url, headers=_headers(), json=payload, timeout=60)
            if 200 <= r.status_code < 300:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** i, 20))
                continue
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
        except Exception as e:
            last_err = e
            time.sleep(min(2 ** i, 20))
    raise RuntimeError(f"OpenAI request failed: {last_err}")

# --- AI 처리 함수 ---
def openai_embed(texts: List[str]) -> List[List[float]]:
    payload = {
        "model": EMBED_MODEL,
        "input": texts,
        "dimensions": EMBED_DIMS,
    }
    data = _retry_post(f"{OPENAI_BASE_URL}/embeddings", payload)
    return [item["embedding"] for item in data["data"]]

def openai_summarize_and_sentiment(title: str, content: str) -> Tuple[str, float]:
    system_instruction = (
        "You are a finance news analyst. "
        "Return JSON only with keys: summary (Korean, <= 2 sentences), sentiment_score (float -1 to 1)."
    )
    user_input = f"[TITLE]\n{title}\n\n[CONTENT]\n{content}"
    payload = {
        "model": SUMMARY_MODEL,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_input}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    data = _retry_post(f"{OPENAI_BASE_URL}/chat/completions", payload)
    out_text = data['choices'][0]['message']['content'].strip()
    try:
        obj = json.loads(out_text)
        return str(obj.get("summary", "")).strip(), max(-1.0, min(1.0, float(obj.get("sentiment_score", 0.0))))
    except:
        return out_text[:300], 0.0

# --- 저장 함수 ---
def postgres_upsert(docs: List[Dict[str, Any]]) -> None:
    if not docs: return
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PWD)
        cur = conn.cursor()
        for d in docs:
            # URLField(200자) 제한 대응
            safe_url = d["original_url"][:200]
            safe_title = d["title"][:255]

            # 1. News 테이블 Upsert
            cur.execute("""
                INSERT INTO news_news (title, content_summary, published_at, sentiment_score, original_url, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (original_url) 
                DO UPDATE SET 
                    content_summary = EXCLUDED.content_summary,
                    sentiment_score = EXCLUDED.sentiment_score
                RETURNING id;
            """, (safe_title, d["content_summary"], d["published_at"], d["sentiment_score"], safe_url))
            
            news_db_id = cur.fetchone()[0]

            # 2. NewsStockMapping 테이블 저장
            # [수정] stocks_stock 테이블의 PK는 'stock_code'입니다.
            # NewsStockMapping 테이블의 외래키 컬럼 이름은 보통 'stock_id'입니다.
            for code in d["stock_codes"]:
                cur.execute("""
                    INSERT INTO news_newsstockmapping (news_id, stock_id)
                    SELECT %s, stock_code 
                    FROM stocks_stock 
                    WHERE stock_code = %s
                    ON CONFLICT (news_id, stock_id) DO NOTHING;
                """, (news_db_id, code))
                
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"❌ Postgres Error: {e}")
    finally:
        if conn: conn.close()

def es_bulk_upsert(docs: List[Dict[str, Any]]) -> None:
    if not docs: return
    lines = []
    for d in docs:
        meta = {"update": {"_index": ES_INDEX, "_id": d["news_id"]}}
        body = {"doc": d, "doc_as_upsert": True}
        lines.append(json.dumps(meta, ensure_ascii=False))
        lines.append(json.dumps(body, ensure_ascii=False))
    bulk_body = "\n".join(lines) + "\n"
    requests.post(f"{ES_BASE_URL}/_bulk", headers={"Content-Type": "application/x-ndjson"}, data=bulk_body.encode("utf-8"), timeout=60)

# --- Spark Partition 처리 ---
def process_partition(rows: Iterator[Row]) -> Iterator[int]:
    batch = []
    count = 0
    for r in rows:
        batch.append(r)
        if len(batch) >= BATCH_SIZE:
            count += _flush_batch(batch)
            batch = []
    if batch:
        count += _flush_batch(batch)
    yield count

def _flush_batch(payload_rows: List[Row]) -> int:
    # 1. Row -> Dict 변환 (AttributeError: get 방지)
    rows_as_dict = [r.asDict() if hasattr(r, "asDict") else r for r in payload_rows]
    
    summaries, sentiments, texts_for_embed = [], [], []
    
    for r in rows_as_dict:
        t = r.get("title") or ""
        # [중요] 본문을 800~1000자로 제한 (요약 품질은 유지하며 비용 급감)
        full_content = r.get("content") or r.get("body") or r.get("text") or ""
        c = full_content[:100] 
        
        summary, score = openai_summarize_and_sentiment(t, c)
        summaries.append(summary)
        sentiments.append(score)
        texts_for_embed.append(f"{t} {summary}")

    # 임베딩 일괄 생성
    vectors = openai_embed(texts_for_embed)

    docs = []
    for r, summary, score, vec in zip(rows_as_dict, summaries, sentiments, vectors):
        # news_id 및 stock_codes 유연한 매핑
        news_id = str(r.get("news_id") or r.get("link") or "")
        stock_codes = r.get("related_stocks") or r.get("stock_codes") or []
        
        docs.append({
            "news_id": news_id,
            "title": r.get("title") or "",
            "content_summary": summary,
            "stock_codes": stock_codes,
            "published_at": r.get("published_at"),
            "sentiment_score": score,
            "embedding": vec,
            "original_url": r.get("link") or r.get("original_url") or ""
        })

    postgres_upsert(docs)
    es_bulk_upsert(docs)
    return len(docs)

# --- 메인 실행부 ---
def main():
    spark = SparkSession.builder.appName("news-ai-batch-kst").getOrCreate()
    target_date_kst = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    target_dt = datetime.strptime(target_date_kst, "%Y-%m-%d")
    
    prev_date = (target_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    
    base_dirs = [
        f"/opt/data-lake/news_enriched/dt={prev_date}",
        f"/opt/data-lake/news_enriched/dt={target_date_kst}"
    ]

    input_paths = []
    for d in base_dirs:
        if os.path.exists(d):
            for root, _, files in os.walk(d):
                if any(f.startswith('part-') for f in files):
                    input_paths.append(root)

    if not input_paths:
        print(f"❌ '{target_date_kst}' 처리할 데이터를 찾을 수 없습니다.")
        return
    
    try:
        df = spark.read.parquet(*list(set(input_paths)))

        # KST 필터링
        df_filtered = df.withColumn("ts", to_timestamp(col("published_at"))) \
                        .withColumn("published_at_kst", from_utc_timestamp(col("ts"), "GMT+9")) \
                        .filter(
                            (col("published_at_kst") >= f"{target_date_kst} 00:00:00") & 
                            (col("published_at_kst") <= f"{target_date_kst} 23:59:59")
                        )

        if df_filtered.count() == 0:
            print(f"⚠️ {target_date_kst} 필터링 결과 데이터가 0건입니다.")
            return

        counts = df_filtered.rdd.mapPartitions(process_partition).collect()
        print(f"✅ [DONE] {target_date_kst} 처리 완료: total={sum(counts)}")

    except Exception as e:
        print(f"❌ 실행 중 에러: {e}")
    finally:
        spark.stop()

if __name__ == "__main__":
    main()