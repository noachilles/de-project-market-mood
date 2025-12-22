# /app/jobs/news_ai_batch.py
import os
import json
import time
from typing import Iterator, List, Dict, Any, Tuple

import requests
from pyspark.sql import SparkSession, Row
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
MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "5"))


def _headers() -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is empty. Set it in environment.")
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }


def _retry_post(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    last_err = None
    for i in range(MAX_RETRIES):
        try:
            r = requests.post(url, headers=_headers(), json=payload, timeout=60)
            if r.status_code >= 200 and r.status_code < 300:
                return r.json()
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


if __name__ == "__main__":
    main()
