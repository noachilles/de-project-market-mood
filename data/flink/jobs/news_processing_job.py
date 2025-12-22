from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode
from pyflink.table import StreamTableEnvironment, EnvironmentSettings, DataTypes
from pyflink.table.udf import udf
import pandas as pd
import os
import json

# ---------------------------------------------------------------
# 1. [사전 준비] 종목 코드 로딩 함수 (UDF에서 쓸 전역 변수)
# ---------------------------------------------------------------
STOCK_DICT = {}

def load_stock_dict():
    """CSV 파일을 읽어서 메모리에 {종목명: 코드} 딕셔너리로 저장"""
    global STOCK_DICT
    # 컨테이너 내부 경로 기준
    csv_path = "/opt/flink/jobs/kospi_code.csv" 
    
    if not STOCK_DICT and os.path.exists(csv_path):
        try:
            print(f"Loading Stock Dictionary from {csv_path}...")
            # pandas로 읽어서 dict로 변환 (속도 최적화)
            df = pd.read_csv(csv_path, encoding='utf-8')
            # { "삼성전자": "005930", "SK하이닉스": "000660", ... } 형태로 변환
            STOCK_DICT = dict(zip(df['한글명'], df['단축코드']))
            print(f"Loaded {len(STOCK_DICT)} stocks.")
        except Exception as e:
            print(f"Error loading stock csv: {e}")

# Job 시작 전에 미리 로딩 시도
load_stock_dict()

# ---------------------------------------------------------------
# 2. [UDF] 종목 매칭 로직 함수
# ---------------------------------------------------------------
@udf(result_type=DataTypes.STRING())
def match_stocks(text):
    """뉴스 제목/본문에 종목명이 있는지 찾아서 JSON 문자열로 반환"""
    if not text or not STOCK_DICT:
        return "[]"
    
    found_stocks = []
    # 단순 매칭: 모든 종목을 순회하며 검색 (개선점: Aho-Corasick 알고리즘 쓰면 더 빠름)
    for name, code in STOCK_DICT.items():
        if name in text:
            found_stocks.append({"name": name, "code": code})
            # 너무 많이 찾으면 느리니까 5개까지만 찾고 중단
            if len(found_stocks) >= 5:
                break
    
    return json.dumps(found_stocks, ensure_ascii=False)


# ---------------------------------------------------------------
# 3. Main Flink Job
# ---------------------------------------------------------------
def main():
    # 환경 설정
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    env.enable_checkpointing(60 * 1000, CheckpointingMode.EXACTLY_ONCE)
    
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    # UDF 등록
    t_env.create_temporary_function("match_stocks", match_stocks)

    # 1. Source: Kafka (news-topic)
    t_env.execute_sql("""
        CREATE TABLE news_source (
            source STRING,
            title STRING,
            link STRING,
            published_at STRING,
            collected_at STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'news-topic',
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'flink-news-group-v2',
            'scan.startup.mode' = 'latest-offset',
            'format' = 'json'
        )
    """)

    # 2. Sink: Parquet (Data Lake) - related_stocks 필드 추가됨!
    t_env.execute_sql("""
        CREATE TABLE parquet_sink (
            source STRING,
            title STRING,
            link STRING,
            published_at STRING,
            related_stocks STRING, -- [핵심] JSON 형태의 문자열로 저장
            dt STRING,
            hr STRING
        ) PARTITIONED BY (dt, hr) WITH (
            'connector' = 'filesystem',
            'path' = 'file:///opt/data-lake/news',
            'format' = 'parquet',
            'sink.partition-commit.delay' = '1 min',
            'sink.partition-commit.policy.kind' = 'success-file'
        )
    """)

    # 3. 실행 로직 (INSERT)
    # title에 종목명이 있는지 검사해서 related_stocks에 넣습니다.
    t_env.execute_sql("""
        INSERT INTO parquet_sink
        SELECT 
            source,
            title,
            link,
            published_at,
            match_stocks(title) as related_stocks, -- UDF 호출
            DATE_FORMAT(CURRENT_TIMESTAMP, 'yyyy-MM-dd') as dt,
            DATE_FORMAT(CURRENT_TIMESTAMP, 'HH') as hr
        FROM news_source
    """)

if __name__ == '__main__':
    main()