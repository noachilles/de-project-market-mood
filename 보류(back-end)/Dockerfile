# Python 3.10 slim 버전 사용
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /back-end

# 라이브러리 설치
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트 소스 코드 복사
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]