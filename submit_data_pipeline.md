MarketMood (AI 기반 실시간 주식 분석 플랫폼)

MarketMood는 실시간 주식 데이터 처리 파이프라인과 RAG(검색 증강 생성) 기반 AI 분석을 결합한 주식 대시보드 프로젝트입니다.
투자자에게 단순 시세 정보뿐 아니라, 뉴스 빅데이터를 분석한 AI 인사이트와 자동 리포트를 제공합니다.

시스템 아키텍처

(발표 자료의 아키텍처 다이어그램 이미지를 여기에 삽입)

Data Pipeline

Kafka: 실시간 데이터 수집

Spark: 데이터 가공 및 분석

HDFS: 분석 데이터 적재

Storage

Redis

실시간 주가 캐싱

Pub/Sub 기반 실시간 스트리밍

Elasticsearch

뉴스 벡터 검색

종목 검색 (RAG 엔진)

PostgreSQL

사용자 정보 및 메타데이터 관리

Backend

Django

REST API

WebSocket 서버

PDF 리포트 생성

Frontend

Vue.js

실시간 차트 렌더링

반응형 대시보드

AI

OpenAI API (LLM)

Elasticsearch Vector Store (RAG)

프로젝트 구조 (Project Structure)
```
de-project/
├── back-end/               # Django REST Framework 서버
│   ├── backend(config)/    # 프로젝트 설정 (urls.py, settings.py)
│   ├── stocks/             # 주식 시세, 차트, 검색 API
│   ├── news/               # 뉴스 크롤링 및 조회 API
│   ├── chat/               # RAG 챗봇 & 리포트 생성 서비스
│   └── manage.py
├── front-end/              # Vue.js 3 (Vite) 클라이언트
│   ├── src/
│   │   ├── components/     # 재사용 가능한 UI 컴포넌트
│   │   ├── views/          # 주요 페이지 (Dashboard, Stocks 등)
│   │   └── api/            # Axios API 호출 모듈
│   └── package.json
├── data/                   # Spark/Hadoop 공유 데이터 볼륨
│   └── spark/jobs/         # Spark 배치 작업 스크립트
├── docker-compose.yml      # 전체 인프라 오케스트레이션
└── README.md               # 프로젝트 문서
```

시작 가이드 (Getting Started)
1. 사전 요구사항 (Prerequisites)

Docker & Docker Compose

Python 3.9+ (로컬 개발 시)

2. 설치 및 실행 (Installation)

프로젝트 루트 디렉토리에서 아래 명령어를 실행합니다.

# 1. 컨테이너 빌드 및 실행 (백그라운드)
docker-compose up -d --build

# 2. 실행 상태 확인
docker ps

3. 초기 데이터 적재 (Data Initialization)

검색 기능(Elasticsearch)을 사용하기 위해 종목 데이터를 먼저 적재해야 합니다.

docker exec -it backend python //app/init_stock_data.py


성공 메시지 예시:

성공! 2xxx개 종목이 Elasticsearch에 저장되었습니다.

사용 방법 (Usage Guide)
1. 웹 서비스 접속
서비스	URL	설명
Frontend	http://localhost:5173
	사용자 대시보드
Backend API	http://localhost:8000
	Django 서버
API Docs	http://localhost:8000/api/docs/
	Swagger API 문서

테스트 계정

ID: test

PW: 1234

2. 데이터 파이프라인 (Spark Jobs)

배치 작업을 수동 실행하거나 테스트할 때 사용합니다.

뉴스 분석 및 벡터 임베딩 배치 실행:

docker exec -it spark-master /opt/spark/bin/spark-submit \
  --master local[*] \
  /app/jobs/news_ai_batch.py

3. 주요 기능 시연 포인트

실시간 주가 확인

대시보드 진입 시 WebSocket + Redis 기반으로 주가 실시간 갱신

AI 종목 검색

상단 검색창에 "삼성" 또는 "005" 입력 시 Elasticsearch 자동완성 검색

뉴스 RAG 챗봇

챗봇에 "최근 삼성전자 이슈 요약해줘" 입력

관련 뉴스 기반으로 AI 답변 생성

주간 리포트 다운로드

"리포트 생성" 버튼 클릭 시 PDF 자동 생성 및 다운로드

API 명세 (API Specification)

본 프로젝트는 Swagger (drf-spectacular) 를 통해 API 문서를 자동화했습니다.

http://localhost:8000/api/docs/

주요 API

GET /api/stocks/search/
주식 종목 검색 (Elasticsearch 기반)

GET /api/stocks/chart/{code}/
캔들스틱 차트 데이터

POST /api/chat/ask/
RAG 기반 질의응답

GET /api/chat/report/
AI 분석 리포트 PDF 다운로드

문제 해결 (Troubleshooting)
Q. 검색이 안 됩니다 (Elasticsearch Error)

init_stock_data.py 실행 여부 확인

docker logs es-container 로 Elasticsearch 상태 확인

Q. Spark Job 실행 시 파일을 찾을 수 없습니다

Windows Git Bash 사용 시 경로 앞에 // 필요

예: //app/jobs/...

실제 파일 위치 확인:

  docker exec -it spark-master find / -name news_ai_batch.py

Tech Stack
Category	Technologies
Frontend	Vue.js 3, Vite, Chart.js / ApexCharts, SCSS
Backend	Django REST Framework, Python
Data Engineering	Apache Spark, Kafka, Hadoop HDFS
Database	PostgreSQL, Redis, Elasticsearch (Vector Search)
AI / LLM	OpenAI API (GPT-4), LangChain
Infra	Docker, Docker Compose