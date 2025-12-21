#!/bin/bash

echo "Producers Container Started (Dummy Mode)"
echo "Waiting for commands..."

# 아무것도 안 하지만 프로세스를 종료하지 않고 무한 대기하는 명령어
tail -f /dev/null