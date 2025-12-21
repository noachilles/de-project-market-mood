# 1. Flink Java 11 이미지 사용
FROM apache/flink:1.17.0-java11

# [중요] 패키지 설치를 위해 root 권한으로 변경
USER root

# 2. Python 3, Pip, wget 설치
# (apt-get update 후 설치 진행)
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip python3-dev wget && \
    ln -s /usr/bin/python3 /usr/bin/python

# 작업 디렉토리 설정
WORKDIR /opt/flink

# 3. PyFlink 및 라이브러리 설치
# (이제 pip3 명령어가 먹힙니다)
RUN pip3 install apache-flink==1.17.0 psycopg2-binary

# 4. 커넥터 JAR 파일 다운로드 (Kafka, JDBC, Postgres)
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-connector-kafka/1.17.0/flink-sql-connector-kafka-1.17.0.jar
# (Parquet 파일 저장용 - [추가됨] 이거 넣으면 나중에 파일 저장할 때 에러 안 남)
RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-sql-parquet/1.17.0/flink-sql-parquet-1.17.0.jar

RUN wget -P /opt/flink/lib/ https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-jdbc/3.1.0-1.17/flink-connector-jdbc-3.1.0-1.17.jar
RUN wget -P /opt/flink/lib/ https://jdbc.postgresql.org/download/postgresql-42.6.0.jar

# 5. 권한 복구 (다시 flink 유저로 실행되도록 설정)
RUN chown -R flink:flink /opt/flink
USER flink