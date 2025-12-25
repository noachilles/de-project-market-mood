# data/spark/Dockerfile

FROM apache/spark:3.5.1

# 1. 관리자 권한으로 변경 (설치를 위해)
USER root

# 2. 라이브러리 설치
RUN pip install --no-cache-dir requests beautifulsoup4 lxml elasticsearch python-dotenv psycopg2-binary

# 3. Elasticsearch Spark Connector JAR 다운로드
RUN mkdir -p /opt/spark/jars && \
    wget -O /opt/spark/jars/elasticsearch-spark-30_2.12-8.11.0.jar https://repo1.maven.org/maven2/org/elasticsearch/elasticsearch-spark-30_2.12/8.11.0/elasticsearch-spark-30_2.12-8.11.0.jar && \
    chmod 644 /opt/spark/jars/elasticsearch-spark-30_2.12-8.11.0.jar

# ★ 핵심 해결책: "UID 185는 spark라는 유저야"라고 OS에 명찰을 달아주는 작업
# 이 줄이 없으면 자바가 "내 이름이 뭐야?" 하다가 죽습니다.
RUN echo "spark:x:185:185:Spark:/opt/spark:/bin/bash" >> /etc/passwd

# 4. Ivy 캐시 디렉토리 생성 (Spark 패키지 다운로드용)
RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars && \
    chown -R 185:185 /home/spark

# 5. 소유권 정리 (혹시 모를 권한 문제 방지)
RUN chown -R 185:185 /opt/spark

# 6. 다시 Spark 유저(UID 185)로 복귀
USER 185