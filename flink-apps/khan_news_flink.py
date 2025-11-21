from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings

def process_khan_news():
    # 1. 환경 설정
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    t_env = StreamTableEnvironment.create(env)

    # 2. Source 설정 (Kafka에서 읽기)
    # (Producer가 보내는 JSON 키값과 똑같이 맞춰주세요)
    t_env.execute_sql("""
        CREATE TABLE source_kafka (
            title STRING,
            link STRING,
            summary STRING,
            content STRING,
            published_at STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'khan-news',  -- (주의) Producer가 보내는 토픽명 확인!
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'flink-khan-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json'
        )
    """)

    # 3. Sink 설정 (가공된 데이터를 보낼 곳)
    # (여기서는 Kafka로 다시 보내지만, 나중에 JDBC(Postgres)로 바꾸기 쉽습니다)
    t_env.execute_sql("""
        CREATE TABLE sink_kafka (
            title STRING,
            link STRING,
            summary STRING,
            content STRING,
            published_at STRING,
            is_processed BOOLEAN  -- [추가] 처리됨 표시
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'processed-khan-news',
            'properties.bootstrap.servers' = 'kafka:9092',
            'format' = 'json'
        )
    """)

    # 4. 데이터 처리 및 전송 (INSERT INTO ... SELECT ...)
    # (process 함수 없이 SQL 안에서 true as is_processed로 해결)
    t_env.execute_sql("""
        INSERT INTO sink_kafka
        SELECT 
            title, 
            link, 
            summary, 
            content, 
            published_at,
            true AS is_processed
        FROM source_kafka
    """)

if __name__ == '__main__':
    process_khan_news()