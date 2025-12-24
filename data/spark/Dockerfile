# data/spark/Dockerfile

FROM apache/spark:3.5.1

# 1. 관리자 권한으로 변경 (설치를 위해)
USER root

# 2. 라이브러리 설치
RUN pip install --no-cache-dir requests beautifulsoup4 lxml elasticsearch psycopg2-binary python-dotenv

# ★ 핵심 해결책: "UID 185는 spark라는 유저야"라고 OS에 명찰을 달아주는 작업
# 이 줄이 없으면 자바가 "내 이름이 뭐야?" 하다가 죽습니다.
RUN echo "spark:x:185:185:Spark:/opt/spark:/bin/bash" >> /etc/passwd

# 3. 소유권 정리 (혹시 모를 권한 문제 방지)
RUN chown -R 185:185 /opt/spark

# 4. 다시 Spark 유저(UID 185)로 복귀
USER 185