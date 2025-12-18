import os
import sys
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings

# 환경변수 가져오기
PG_USER = os.getenv('POSTGRES_USER')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD')

# ❌ None 값 체크 로직 추가 ❌
if not PG_USER or not PG_PASSWORD:
    print("FATAL ERROR: POSTGRES_USER 또는 POSTGRES_PASSWORD 환경 변수가 설정되지 않았습니다.")
    # Flink 작업이 실행되기 전에 확실히 종료
    sys.exit(1)

PG_DB = os.getenv('POSTGRES_DB')
PG_HOST = os.getenv('POSTGRES_HOST', 'postgres')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')

def main():
    # 1. 환경 설정
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)
    t_env = StreamTableEnvironment.create(env)

    # JAR 파일 의존성 추가 (Kafka, JDBC, Postgres 등)
    # 로컬/컨테이너 경로에 맞게 수정 필요
    # t_env.get_config().get_configuration().set_string(
    #     "pipeline.jars", 
    #     "file:///opt/flink/lib/flink-sql-connector-kafka-3.0.0-1.18.jar;file:///opt/flink/lib/flink-connector-jdbc-3.1.2-1.18.jar;file:///opt/flink/lib/postgresql-42.6.0.jar"
    # )

    # 2. Kafka Source 테이블 정의 (Producer 데이터 구조와 100% 일치해야 함)
    create_kafka_source_ddl = """
        CREATE TABLE kafka_source (
            title STRING,
            link STRING,
            content STRING,
            published_at STRING,  -- Producer가 문자열로 보냄
            source STRING,
            summary STRING,
            sentiment STRING,
            keywords STRING,
            related_symbols STRING,
            reason STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'news_topic',  -- Producer의 토픽명
            'properties.bootstrap.servers' = 'kafka:9092',
            'properties.group.id' = 'news_flink_group',
            'scan.startup.mode' = 'earliest-offset', -- 처음부터 다 읽기
            'format' = 'json',
            'json.fail-on-missing-field' = 'false', -- 필드 없어도 에러 안 나게
            'json.ignore-parse-errors' = 'true'     -- 파싱 에러 무시
        )
    """
    t_env.execute_sql(create_kafka_source_ddl)

    # 3. DB Sink 테이블 정의 (PostgreSQL 예시)
    # DB에 미리 테이블이 생성되어 있어야 합니다.
    create_db_sink_ddl = f"""
        CREATE TABLE db_sink (
            title STRING,
            link STRING,
            content STRING,
            published_at TIMESTAMP(3), -- DB 타입에 맞춤
            source_name STRING,
            summary STRING,
            sentiment STRING,
            keywords STRING,
            related_symbols STRING,
            reason STRING,
            created_at TIMESTAMP(3) -- 수집 시간
        ) WITH (
            'connector' = 'jdbc',
            'url' = 'jdbc:postgresql://{PG_HOST}:{PG_PORT}/{PG_DB}',
            'table-name' = 'news',
            'username' = '{PG_USER}',
            'password' = '{PG_PASSWORD}'
        )
    """
    t_env.execute_sql(create_db_sink_ddl)

    # 4. 데이터 이동 및 변환 (Kafka -> DB)
    # published_at 문자열을 TIMESTAMP로 변환하는 과정 포함
    insert_query = """
    INSERT INTO db_sink
    SELECT 
        title,
        link,
        content,
        TO_TIMESTAMP(published_at), -- [중요] String -> Timestamp 변환
        source,
        summary,
        sentiment,
        keywords,
        related_symbols,
        reason,
        CURRENT_TIMESTAMP -- DB 저장 시점
    FROM kafka_source
    """
    
    t_env.execute_sql(insert_query)

if __name__ == '__main__':
    main()