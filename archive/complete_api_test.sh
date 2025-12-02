#!/bin/bash

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║       LangGraph 办公智能体 - 完整API接口测试                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "测试地址: http://localhost:8000"
echo "测试时间: $(date)"
echo ""

PASS=0
FAIL=0

# 测试函数
test_endpoint() {
    local desc="$1"
    local cmd="$2"
    local expected="${3:-}"
    
    echo -n "  $desc ... "
    
    output=$(eval "$cmd" 2>&1)
    exit_code=$?
    
    # 检查是否成功
    if [ "$exit_code" -eq 0 ]; then
        # 如果有期望内容，检查是否包含
        if [ -n "$expected" ] && echo "$output" | grep -q "$expected"; then
            echo "✓ 通过"
            ((PASS++))
            return 0
        elif [ -z "$expected" ]; then
            echo "✓ 通过"
            ((PASS++))
            return 0
        else
            echo "✗ 失败 (期望包含: $expected)"
            ((FAIL++))
            return 1
        fi
    else
        echo "✗ 失败 (退出码: $exit_code)"
        echo "    错误: $output"
        ((FAIL++))
        return 1
    fi
}

echo "📊 第一阶段: GET 接口测试"
echo "---------------------------------------------------------------"
test_endpoint "1.1 首页" "curl -s -o /dev/null -w \"%{http_code}\" http://localhost:8000/ | grep -q '200'"
echo "       └─ 页面长度: $(curl -s http://localhost:8000/ | wc -c) bytes"

test_endpoint "1.2 健康检查" "curl -s http://localhost:8000/health | jq -r '.status' | grep -q 'healthy'"
test_endpoint "1.3 API信息" "curl -s http://localhost:8000/api/info | jq -r '.version' | grep -q '1.0.0'"
test_endpoint "1.4 支持的格式" "curl -s http://localhost:8000/supported-formats | jq -r '.success' | grep -q 'true'"
echo "       └─ 支持 $(curl -s http://localhost:8000/supported-formats | jq -r '.formats | length') 种格式"

test_endpoint "1.5 最近的文件" "curl -s http://localhost:8000/recent-files | jq -r '.success' | grep -q 'true'"
echo ""

echo "📁 第二阶段: 文档上传测试"
echo "---------------------------------------------------------------"
echo ""

# 创建测试文件
if [ ! -f "test_sample.txt" ]; then
    cat > test_sample.txt << 'TESTEOF'
这是一份测试文档。

主要内容包括：
1. 2024年营收达到1000万人民币
2. 团队规模扩展到50人
3. 客户满意度达到95%

如有问题请联系：test@example.com 或致电 138-0000-0000
我们需要在2025-01-15前完成项目交付。
TESTEOF
fi

echo "  2.1 上传文档并总结"
echo "       文档大小: $(wc -c < test_sample.txt) bytes"
echo "       操作类型: summarize"
echo ""

RESPONSE=$(curl -s -F "file=@test_sample.txt" -F "operation=summarize" http://localhost:8000/upload)
UPLOAD_STATUS=$?

echo "       响应状态: $([ $UPLOAD_STATUS -eq 0 ] && echo '成功' || echo '失败')"
echo "       处理状态: $(echo "$RESPONSE" | jq -r '.success // false)'"
echo "       消息: $(echo "$RESPONSE" | jq -r '.message // "N/A"')"
echo ""

# 检查是否有结果预览
PREVIEW=$(echo "$RESPONSE" | jq -r '.result_preview // "null"')
if [ "$PREVIEW" != "null" ]; then
    echo "       结果预览:"
    echo "       $(echo "$PREVIEW" | head -3 | sed 's/^/       /')"
    echo "       ..."
    ((PASS++))
else
    echo "       ⚠️  无结果预览"
    ((FAIL++))
fi

echo ""
echo "📋 第三阶段: 其他操作类型测试"
echo "---------------------------------------------------------------"

OPERATIONS=("generate" "convert" "extract_table")
for op in "${OPERATIONS[@]}"; do
    echo -n "  3.$op 操作... "
    RESP=$(curl -s -F "file=@test_sample.txt" -F "operation=$op" -F "instruction=简短说明" http://localhost:8000/upload)
    if echo "$RESP" | jq -r '.success' | grep -q 'true'; then
        echo "✓"
        ((PASS++))
    else
        ERROR=$(echo "$RESP" | jq -r '.error' 2>/dev/null || echo "未知错误")
        echo "✗ ($ERROR)"
        ((FAIL++))
    fi
done

echo ""
echo "🗑️  第四阶段: 清理测试"
echo "---------------------------------------------------------------"
test_endpoint "4.1 清理上传文件" "curl -s -X DELETE http://localhost:8000/clear-uploads | jq -r '.success' | grep -q 'true'"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                          测试总结                                ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "  总测试数: $((PASS + FAIL))"
echo "  通过数: \033[0;32m$PASS\033[0m"
echo "  失败数: \033[0;31m$FAIL\033[0m"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "  🎉 所有接口测试成功！"
    exit 0
else
    echo "  ⚠️  有 $FAIL 个测试失败"
    exit 1
fi
