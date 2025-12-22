# 1. Flink Java 11 이미지 사용
FROM apache/flink:1.17.0-java11

# [중요] 패키지 설치를 위해 root 권한으로 변경
USER root

# 2. Python 3, Pip, wget 설치
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev wget && \
    ln -s /usr/bin/python3 /usr/bin/python

# 작업 디렉토리 설정
WORKDIR /opt/flink

# 3. PyFlink 및 라이브러리 설치
RUN pip3 install apache-flink==1.17.0 psycopg2-binary

# 4. 커넥터 JAR 파일 다운로드
# (1) Kafka 연결용
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.17.0/flink-sql-connector-kafka-1.17.0.jar

# (2) Parquet 저장용 (핵심! Hadoop 의존성 추가)
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-parquet/1.17.0/flink-sql-parquet-1.17.0.jar
# [추가됨] Parquet 쓰기 작업을 위해 꼭 필요한 Hadoop 라이브러리
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-shaded-hadoop-2-uber/2.8.3-10.0/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar

# (3) Postgres/JDBC 연결용
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.0-1.17/flink-connector-jdbc-3.1.0-1.17.jar
RUN wget -P /opt/flink/lib/ https://jdbc.postgresql.org/download/postgresql-42.6.0.jar

# 5. 권한 복구
RUN chown -R flink:flink /opt/flink
USER flink