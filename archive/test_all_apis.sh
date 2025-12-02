#!/bin/bash
echo "╔══════════════════════════════════════════════════╗"
echo "║     LangGraph 办公智能体 - API 全面测试          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 测试1: 首页
echo "📄 测试1: GET / (首页)"
curl -s -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n" -o /tmp/test1.html http://localhost:8000/
echo ""

# 测试2: 健康检查
echo "🏥 测试2: GET /health (健康检查)"
curl -s http://localhost:8000/health | jq .
echo ""

# 测试3: API信息
echo "ℹ️  测试3: GET /api/info (API信息)"
curl -s http://localhost:8000/api/info | jq .
echo ""

# 测试4: 支持的格式
echo "📋 测试4: GET /supported-formats (支持的格式)"
curl -s http://localhost:8000/supported-formats | jq .
echo ""

# 测试5: 最近的文件
echo "📂 测试5: GET /recent-files (最近的文件)"
curl -s http://localhost:8000/recent-files | jq .
echo ""

# 测试6: 上传和总结（如果文件存在）
if [ -f "test文档.txt" ]; then
    echo "☁️  测试6: POST /upload (上传并处理 - 总结)"
    TIMEOUT=120
    timeout $TIMEOUT curl -s -w "\n状态码: %{http_code}\n耗时: %{time_total}s\n" -F "file=@test文档.txt" -F "operation=summarize" -F "instruction=提取关键数据" http://localhost:8000/upload
    echo ""
else
    echo "⚠️  test文档.txt 不存在，跳过上传测试"
    echo ""
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║           测试完成！                              ║"
echo "╚══════════════════════════════════════════════════╝"
