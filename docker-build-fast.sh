#!/bin/bash
# 빠른 빌드 스크립트 - Step 1용 (backend만)

echo "🚀 Step 1용 빠른 빌드 시작 (backend만)"
docker-compose build backend

echo "✅ 빌드 완료! 이제 컨테이너를 시작하세요:"
echo "   docker-compose up -d postgres redis backend"

