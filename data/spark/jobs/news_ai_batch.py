# /app/jobs/news_ai_batch.py
import os
import json
import time
from typing import Iterator, List, Dict, Any, Tuple

import requests
from pyspark.sql import SparkSession, Row
<<<<<<< HEAD
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
=======
from pyspark.sql.functions import col, concat_ws, coalesce, lit

OPENAI_BASE_URL = "https://api.openai.com/v1"
ES_BASE_URL = os.getenv("ES_BASE_URL", "http://elasticsearch:9200")
ES_INDEX = os.getenv("ES_INDEX", "news-ai-vector")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
EMBED_DIMS = int(os.getenv("EMBED_DIMS", "1536"))  # ES dims에 맞춰 1536 권장
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-4.1-mini")  # 가벼운 모델로 시작 추천

# 비용/속도용 튜닝
BATCH_SIZE = int(os.getenv("AI_BATCH_SIZE", "16"))      # OpenAI API 호출 배치
SLEEP_BETWEEN_CALLS = float(os.getenv("AI_SLEEP", "0.0"))
>>>>>>> parent of 79a31d5 (Merge branch 'MM-32' of https://lab.ssafy.com/dtmg1ejk/de-project into MM-32)
MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "5"))


def _headers() -> Dict[str, str]:
<<<<<<< HEAD
    # Worker 내부 유실 방지를 위해 os.environ에서 직접 조회
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv("/app/.env")
        api_key = os.environ.get("OPENAI_API_KEY")
=======
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is empty. Set it in environment.")
>>>>>>> parent of 79a31d5 (Merge branch 'MM-32' of https://lab.ssafy.com/dtmg1ejk/de-project into MM-32)
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
<<<<<<< HEAD
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
=======
            # 429/5xx 재시도
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** i, 20))
                continue
            # 그 외는 바로 에러
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
        except Exception as e:
            last_err = e
            time.sleep(min(2 ** i, 20))
    raise RuntimeError(f"OpenAI request failed after retries: {last_err}")


def openai_embed(texts: List[str]) -> List[List[float]]:
    """
    /v1/embeddings
    - model: text-embedding-3-large
    - dimensions: 1536 (ES 매핑과 맞추기)
    """
    payload = {
        "model": EMBED_MODEL,
        "input": texts,
        "dimensions": EMBED_DIMS,
    }
    data = _retry_post(f"{OPENAI_BASE_URL}/embeddings", payload)
    # data["data"] 는 input 순서대로 list
    return [item["embedding"] for item in data["data"]]


def openai_summarize_and_sentiment(title: str, content: str) -> Tuple[str, float]:
    """
    /v1/responses 로 "요약 + 감정점수(-1~1)"를 JSON으로 받기
    """
    instruction = (
        "You are a finance news analyst. "
        "Return JSON only with keys: summary (Korean, <= 2 sentences), sentiment_score (float -1 to 1)."
    )
    user_input = f"[TITLE]\n{title}\n\n[CONTENT]\n{content}"

    payload = {
        "model": SUMMARY_MODEL,
        "instructions": instruction,
        "input": user_input,
        "text": {"format": {"type": "text"}},
        "temperature": 0.2,
        "max_output_tokens": 200,
    }
    data = _retry_post(f"{OPENAI_BASE_URL}/responses", payload)

    # 문서 예시처럼 output -> message -> content -> output_text 텍스트를 뽑는다
    # :contentReference[oaicite:3]{index=3}
    out_text = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    out_text += c.get("text", "")
    out_text = out_text.strip()

    # JSON only 강제했으니 파싱
    try:
        obj = json.loads(out_text)
        summary = str(obj.get("summary", "")).strip()
        score = float(obj.get("sentiment_score", 0.0))
        # clamp
        score = max(-1.0, min(1.0, score))
        return summary, score
    except Exception:
        # 실패 시 fallback
        return out_text[:300], 0.0


def es_bulk_upsert(docs: List[Dict[str, Any]]) -> None:
    """
    Elasticsearch _bulk update(doc_as_upsert)
    """
    if not docs:
        return

    lines = []
    for d in docs:
        _id = d["news_id"]
        meta = {"update": {"_index": ES_INDEX, "_id": _id}}
        body = {"doc": d, "doc_as_upsert": True}
        lines.append(json.dumps(meta, ensure_ascii=False))
        lines.append(json.dumps(body, ensure_ascii=False))

    bulk_body = "\n".join(lines) + "\n"
    r = requests.post(
        f"{ES_BASE_URL}/_bulk",
        headers={"Content-Type": "application/x-ndjson"},
        data=bulk_body.encode("utf-8"),
        timeout=60,
    )
    if r.status_code < 200 or r.status_code >= 300:
        raise RuntimeError(f"ES bulk failed {r.status_code}: {r.text[:500]}")
    resp = r.json()
    if resp.get("errors"):
        # 어떤 문서가 실패했는지 최소한만 출력
        items = resp.get("items", [])
        bad = [it for it in items if list(it.values())[0].get("error")]
        raise RuntimeError(f"ES bulk had errors. sample={bad[:2]}")


def process_partition(rows: Iterator[Row]) -> Iterator[int]:
    """
    Spark executor에서 partition 단위 처리:
    - rows -> batch
    - summary/sentiment + embedding
    - ES upsert
    """
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


def _flush_batch(batch: List[Row]) -> int:
    texts = []
    payload_rows = []

    for r in batch:
        title = r["title"] or ""
        content = r["content"] or ""
        combined = f"{title}\n\n{content}".strip()
        texts.append(combined)
        payload_rows.append(r)

    # 1) 요약/감정
    summaries = []
    sentiments = []
    for r in payload_rows:
        s, sc = openai_summarize_and_sentiment(r["title"] or "", r["content"] or "")
        summaries.append(s)
        sentiments.append(sc)
        if SLEEP_BETWEEN_CALLS:
            time.sleep(SLEEP_BETWEEN_CALLS)

    # 2) 임베딩 (배치 호출)
    vectors = openai_embed(texts)
    if SLEEP_BETWEEN_CALLS:
        time.sleep(SLEEP_BETWEEN_CALLS)

    # 3) ES 문서 구성 + upsert
    docs = []
    for r, summary, score, vec in zip(payload_rows, summaries, sentiments, vectors):
        docs.append({
            "news_id": r["news_id"],
            "title": r["title"],
            "content_summary": summary,
            "stock_codes": r["stock_codes"] or [],
            "published_at": r["published_at"],  # 문자열/타임스탬프 모두 가능(ES date 파서가 처리)
            "sentiment_score": score,
            "embedding": vec,
        })

    es_bulk_upsert(docs)
    return len(docs)


def main():
    input_path = os.getenv("INPUT_PATH", "/app/lake/news_raw/*.parquet")

    spark = (
        SparkSession.builder
        .appName("news-ai-batch")
        .getOrCreate()
    )

    # Parquet 스키마 예시:
    # news_id, title, content, stock_codes(array<string>), published_at
    df = spark.read.parquet(input_path).select(
        col("news_id"),
        col("title"),
        col("content"),
        col("stock_codes"),
        col("published_at"),
    ).where(col("news_id").isNotNull())

    # executor에서 requests/OpenAI를 쓰므로 RDD로 내리고 partition 처리
    counts = df.rdd.mapPartitions(process_partition).collect()
    total = sum(counts)
    print(f"[DONE] processed={total} input_path={input_path} index={ES_INDEX}")

>>>>>>> parent of 79a31d5 (Merge branch 'MM-32' of https://lab.ssafy.com/dtmg1ejk/de-project into MM-32)

if __name__ == "__main__":
    main()
