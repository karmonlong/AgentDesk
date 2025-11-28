#!/bin/bash

echo "测试1: 基本对话"
curl -X POST http://localhost:8000/api/chat \
  -F "message=帮我总结这段文字的要点" \
  -s | python -m json.tool | head -50

echo ""
echo "================================"
echo "测试2: @ 提及特定智能体"
echo "================================"

# 使用 --data-urlencode 来正确处理 @
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "message=@翻译专家 请帮我翻译 Hello World" \
  -s | python -m json.tool | head -50

