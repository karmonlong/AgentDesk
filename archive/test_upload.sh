#!/bin/bash

echo "=== 测试上传功能 (POST /upload) ==="
echo ""

# 检查测试文件是否存在
if [ ! -f "test文档.txt" ]; then
    echo "创建测试文件..."
    cat > test文档.txt << 'ENDFILE'
这是一份测试文档。

主要内容包括：
1. 2024年营收达到1000万人民币
2. 团队规模扩展到50人
3. 客户满意度达到95%

如有问题请联系：test@example.com 或致电 138-0000-0000
ENDFILE
    echo "✓ 测试文件已创建"
fi

echo "开始上传并处理..."
echo ""

# 调用API
RESPONSE=$(curl -s -F "file=@test文档.txt" -F "operation=summarize" -F "instruction=提取关键数据" http://localhost:8000/upload)

# 显示响应
echo "响应:"
echo "$RESPONSE" | jq .
echo ""

# 检查结果
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✓ 上传和处理成功！"
    
    # 获取结果预览
    PREVIEW=$(echo "$RESPONSE" | jq -r '.result_preview' 2>/dev/null | head -5)
    echo "结果预览:"
    echo "$PREVIEW"
    echo "..."
else
    echo "✗ 上传或处理失败"
    ERROR=$(echo "$RESPONSE" | jq -r '.error' 2>/dev/null)
    echo "错误: $ERROR"
fi

echo ""
echo "==================================="
