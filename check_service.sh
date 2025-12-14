#!/bin/bash
# 检查服务状态和日志

echo "=== 服务进程状态 ==="
ps aux | grep "uvicorn.*app:app" | grep -v grep

echo -e "\n=== 端口监听状态 ==="
lsof -i :8000 | head -5

echo -e "\n=== 健康检查 ==="
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "健康检查失败"

echo -e "\n=== 最近日志（最后20行）==="
tail -20 app.log 2>/dev/null || tail -20 server.log 2>/dev/null || echo "无日志文件"

echo -e "\n=== 测试主页响应 ==="
timeout 5 curl -s -o /dev/null -w "状态码: %{http_code}\n响应时间: %{time_total}s\n" http://localhost:8000/

echo -e "\n=== 测试API端点 ==="
echo "测试 /api/agents:"
timeout 3 curl -s http://localhost:8000/api/agents | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'成功: {d.get(\"success\")}, 智能体数量: {len(d.get(\"agents\", []))}')" 2>/dev/null || echo "API调用失败"

echo -e "\n测试 /api/files:"
timeout 3 curl -s http://localhost:8000/api/files | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'成功: {d.get(\"success\")}, 文件数量: {len(d.get(\"files\", []))}')" 2>/dev/null || echo "API调用失败"













