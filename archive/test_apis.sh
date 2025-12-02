#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║      LangGraph 办公智能体 - 接口测试报告                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo "测试时间: $(date)"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果数组
declare -a results

# 测试函数
test_api() {
    local name="$1"
    local url="$2"
    local method="${3:-GET}"
    
    echo -n "正在测试: $name ... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" "$url" 2>&1)
    else
        response=$(curl -s -w "\nHTTP_CODE:%{http_code}\nTIME:%{time_total}" -X POST "$url" 2>&1)
    fi
    
    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    time=$(echo "$response" | grep "TIME:" | cut -d: -f2)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ 通过${NC} (耗时: ${time}s)"
        results+=("✓ $name: 通过")
        return 0
    else
        echo -e "${RED}✗ 失败${NC} (状态码: $http_code, 耗时: ${time}s)"
        results+=("✗ $name: 失败 (状态码: $http_code)")
        return 1
    fi
}

# 测试所有接口
echo "📋 开始测试所有接口..."
echo ""

test_api "1. 首页" "http://localhost:8000/"
test_api "2. 健康检查" "http://localhost:8000/health"
test_api "3. API信息" "http://localhost:8000/api/info"
test_api "4. 支持的格式" "http://localhost:8000/supported-formats"
test_api "5. 最近的文件" "http://localhost:8000/recent-files"

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                         测试总结                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

# 统计结果
total=${#results[@]}
passed=$(printf '%s\n' "${results[@]}" | grep -c "✓")
failed=$((total - passed))

echo "总测试数: $total"
echo -e "通过: ${GREEN}$passed${NC}"
echo -e "失败: ${RED}$failed${NC}"
echo ""

# 显示详细结果
echo "详细结果:"
printf '%s\n' "${results[@]}"

# 测试总结
if [ $failed -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 所有接口测试通过！${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  有 $failed 个接口测试失败${NC}"
    exit 1
fi
