FROM python:3.9-slim

WORKDIR /app

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# [핵심] 컨테이너가 바로 꺼지지 않고 계속 살아있게 함 (테스트용)
# 이렇게 해두면 우리가 원할 때 들어와서 스크립트를 실행할 수 있습니다.
# CMD ["/bin/bash", "run.sh"]

# 실행 (print 문이 로그에 즉시 찍히게 -u 옵션 사용)
CMD ["python", "-u", "news_producer.py"]