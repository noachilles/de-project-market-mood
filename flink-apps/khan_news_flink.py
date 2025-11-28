from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment

def process_news_to_db():
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    t_env = StreamTableEnvironment.create(env)

    # 1. Source: Kafka (뉴스 읽기)
    t_env.execute_sql("""
        CREATE TABLE source_kafka (
            title STRING,
            link STRING,
            summary STRING,
            content STRING,
            published_at STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'khan-news',  -- Producer가 보내는 토픽명 확인
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'flink-db-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    # 2. Sink: PostgreSQL (DB 저장)
    # (테이블명: feeds_news, 유저/비번: postgres/postgres)
    t_env.execute_sql("""
        CREATE TABLE sink_postgres (
            title STRING,
            link STRING,
            summary STRING,
            content STRING,
            published_at TIMESTAMP(3)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/postgres',
            'table-name' = 'feeds_news',
            'username' = 'postgres',
            'password' = 'postgres'
        )
    """)

    # 3. 데이터 이동 (String 날짜 -> Timestamp 변환)
    # TO_TIMESTAMP 함수로 날짜 포맷을 맞춰줍니다. (Producer 형식에 따라 수정 필요)
    # 예: "2023-11-21T08:00:00Z" 형태라면 아래 포맷 사용
    t_env.execute_sql("""
        INSERT INTO sink_postgres
        SELECT 
            title,
            link,
            summary,
            content,
            TO_TIMESTAMP(published_at, 'yyyy-MM-ddTHH:mm:ss') 
        FROM source_kafka
    """)

if __name__ == '__main__':
    process_news_to_db()