# Python 3.10 slim 버전 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 1. 필수 패키지 설치 (Postgres 등을 위해 필요한 OS 레벨 패키지)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트 소스 코드 복사
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]