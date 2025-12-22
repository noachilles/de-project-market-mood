#!/bin/bash
set -e

echo "Producers Container Started (RUN MODE)"
cd /app

# ✅ 실제 producer 실행
python producer_with_AI.py
