from pyflink.datastream import StreamExecutionEnvironment, CheckpointingMode, RuntimeExecutionMode
from pyflink.table import StreamTableEnvironment, EnvironmentSettings, DataTypes
from pyflink.table.udf import udf
import pandas as pd
import os
import json

# ---------------------------------------------------------------
# 1. [사전 준비] 종목 코드 로딩
# ---------------------------------------------------------------
STOCK_DICT = {}

def load_stock_dict():
    """CSV 파일을 읽어서 메모리에 {종목명: 코드} 딕셔너리로 저장"""
    global STOCK_DICT
    csv_path = "/opt/flink/jobs/kospi_code.csv"
    
    if not STOCK_DICT and os.path.exists(csv_path):
        try:
            print(f"Loading Stock Dictionary from {csv_path}...")
            df = pd.read_csv(csv_path, encoding='utf-8')
            STOCK_DICT = dict(zip(df['한글명'], df['단축코드']))
            print(f"Loaded {len(STOCK_DICT)} stocks.")
        except Exception as e:
            print(f"Error loading stock csv: {e}")

load_stock_dict()

# ---------------------------------------------------------------
# 2. [UDF] 종목 매칭 로직
# ---------------------------------------------------------------
@udf(result_type=DataTypes.STRING())
def match_stocks(text):
    if not text or not STOCK_DICT:
        return "[]"
    
    found_stocks = []
    for name, code in STOCK_DICT.items():
        if name in text:
            found_stocks.append({"name": name, "code": code})
            if len(found_stocks) >= 5: break
    
    return json.dumps(found_stocks, ensure_ascii=False)


# ---------------------------------------------------------------
# 3. Main Flink Job
# ---------------------------------------------------------------
def main():
    # 환경 설정
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    env.set_runtime_mode(RuntimeExecutionMode.STREAMING)
    env.enable_checkpointing(60 * 1000, CheckpointingMode.EXACTLY_ONCE)
    
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, environment_settings=settings)

    # UDF 등록
    t_env.create_temporary_function("match_stocks", match_stocks)

    # 1. Source: Kafka
    t_env.execute_sql("""
        CREATE TABLE news_source (
            source STRING,
            title STRING,
            link STRING,
            published_at STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'news-topic',
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'flink-news-es-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    # 2. Sink A: Parquet (Data Lake) - 백업용
    t_env.execute_sql("""
        CREATE TABLE parquet_sink (
            source STRING,
            title STRING,
            link STRING,
            published_at STRING,
            related_stocks STRING,
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

    # 3. Sink B: Elasticsearch (Search Engine) - 검색 서비스용
    # 주의: hosts는 docker-compose 서비스명(elasticsearch) 사용
    t_env.execute_sql("""
        CREATE TABLE es_sink (
            source STRING,
            title STRING,
            link STRING,
            published_at STRING,
            related_stocks STRING  -- JSON 문자열 그대로 저장
        ) WITH (
            'connector' = 'elasticsearch-7',
            'hosts' = 'http://elasticsearch:9200',
            'index' = 'news-raw',
            'format' = 'json',
            'sink.bulk-flush.max-actions' = '1'  -- 데이터 들어오면 바로바로 넣기 (테스트용)
        )
    """)

    # 4. 멀티 싱크 실행 (Source -> [Parquet, ES])
    statement_set = t_env.create_statement_set()

    # 4-1. Parquet로 보내기
    statement_set.add_insert_sql("""
        INSERT INTO parquet_sink
        SELECT 
            source, title, link, published_at,
            match_stocks(title),
            DATE_FORMAT(CURRENT_TIMESTAMP, 'yyyy-MM-dd'),
            DATE_FORMAT(CURRENT_TIMESTAMP, 'HH')
        FROM news_source
    """)

    # 4-2. Elasticsearch로 보내기
    statement_set.add_insert_sql("""
        INSERT INTO es_sink
        SELECT 
            source, title, link, published_at,
            match_stocks(title)
        FROM news_source
    """)

    statement_set.execute()

if __name__ == '__main__':
    main()