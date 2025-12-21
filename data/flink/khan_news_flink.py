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
            published_at STRING  -- Producer가 보내는 원본 날짜 문자열
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'news_articles',  -- [수정 1] Producer 토픽명과 일치시킴
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'flink-db-group',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json',
            'json.fail-on-missing-field' = 'false', -- (안전장치) 없는 필드는 무시
            'json.ignore-parse-errors' = 'true'     -- (안전장치) 파싱 에러 무시
        )
    """)

    # 2. Sink: PostgreSQL (DB 저장)
    # (주의: DB 접속 정보가 docker-compose.yml과 일치해야 함)
    t_env.execute_sql("""
        CREATE TABLE sink_postgres (
            title STRING,
            link STRING,
            summary STRING,
            content STRING,
            published_at TIMESTAMP(3)
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://postgres:5432/postgres', -- [확인필요] DB이름
            'table-name' = 'news',  -- back-end/feeds/models.py의 News/Meta 확인
            'username' = 'ssafyuser',  -- [확인필요] 유저명
            'password' = 'ssafy'   -- [확인필요] 비밀번호
        )
    """)

    # 3. 데이터 이동 (날짜 포맷 수정)
    # [수정 2] 'X'는 +09:00이나 Z 같은 타임존을 처리해줍니다.
    t_env.execute_sql("""
        INSERT INTO sink_postgres
        SELECT 
            title,
            link,
            summary,
            content,
            TO_TIMESTAMP(published_at, 'yyyy-MM-dd''T''HH:mm:ssXXX') - INTERVAL '9' HOUR
        FROM source_kafka
    """)

if __name__ == '__main__':
    process_news_to_db()