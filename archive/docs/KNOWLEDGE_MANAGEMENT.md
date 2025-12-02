# AgentDesk 知识管理功能使用指南

## 概述

AgentDesk 的知识管理功能基于**向量检索技术（RAG）**，可以实现：
- 文档智能存储和检索
- 多文档关联分析
- 基于知识库的智能问答
- 跨文档信息综合

## 核心组件

### 1. 知识管理专家智能体

**名称**：知识管理专家  
**图标**：📚 (fas fa-book-open)  
**角色**：文档知识库与检索专家

**核心能力**：
- 文档向量化存储和智能检索
- 多文档关联分析和对比
- 基于知识库的智能问答（RAG）
- 跨文档信息综合和提炼
- 知识关联和脉络梳理

### 2. 向量存储引擎

**技术栈**：
- **向量数据库**：ChromaDB
- **嵌入模型**：Google Gemini embedding-001
- **文本分割器**：RecursiveCharacterTextSplitter
- **相似度检索**：向量余弦相似度

**存储位置**：`./chroma_db/`

## API 接口

### 1. 添加文档到知识库

```bash
POST /api/knowledge/add

# 示例
curl -X POST -F "file=@document.pdf" http://localhost:8000/api/knowledge/add
```

**响应**：
```json
{
  "success": true,
  "message": "文档已添加到知识库",
  "doc_id": "5f90edea48af619d92ee28792429c918",
  "chunks_count": 15
}
```

### 2. 搜索知识库

```bash
POST /api/knowledge/search

# 示例
curl -X POST \
  -d "query=AgentDesk有哪些功能" \
  -d "k=5" \
  http://localhost:8000/api/knowledge/search
```

**参数**：
- `query`：查询文本（必填）
- `k`：返回结果数量（默认 5）

**响应**：
```json
{
  "success": true,
  "query": "AgentDesk有哪些功能",
  "results": [
    {
      "content": "文档内容片段...",
      "metadata": {
        "source": "document.pdf",
        "doc_id": "...",
        "chunk_index": 0
      },
      "similarity_score": 0.87
    }
  ],
  "count": 5
}
```

### 3. 列出知识库文档

```bash
GET /api/knowledge/list

# 示例
curl http://localhost:8000/api/knowledge/list
```

### 4. 获取文档详情

```bash
GET /api/knowledge/{doc_id}

# 示例
curl http://localhost:8000/api/knowledge/5f90edea48af619d92ee28792429c918
```

### 5. 删除文档

```bash
DELETE /api/knowledge/{doc_id}

# 示例
curl -X DELETE http://localhost:8000/api/knowledge/5f90edea48af619d92ee28792429c918
```

## 使用场景

### 场景 1：构建企业知识库

```bash
# 1. 上传多个文档
curl -X POST -F "file=@投资策略报告.pdf" http://localhost:8000/api/knowledge/add
curl -X POST -F "file=@行业分析.docx" http://localhost:8000/api/knowledge/add
curl -X POST -F "file=@监管政策文件.pdf" http://localhost:8000/api/knowledge/add

# 2. 查询知识库
curl -X POST -d "query=最新的投资策略是什么" -d "k=5" http://localhost:8000/api/knowledge/search
```

### 场景 2：智能问答

与知识管理专家对话：

```
用户: @知识管理专家 AgentDesk 有哪些核心功能？

知识管理专家: 根据知识库检索，AgentDesk 的核心功能包括：
1. 文档分析：自动提取关键信息和数据
2. 内容创作：生成专业的投资报告
3. 数据分析：处理财务数据
4. 翻译服务：中英文专业翻译
5. 合规检查：监管合规审核
6. 知识管理：基于向量检索的智能问答

[来源：test_knowledge.txt, 相似度: 0.87]
```

### 场景 3：多文档对比分析

```
用户: @知识管理专家 对比 2023 和 2024 年的投资策略有什么变化？

知识管理专家: 通过检索相关文档，我发现：

**2023年策略**：
- 重点关注科技板块...
[来源：2023投资策略.pdf]

**2024年策略**：
- 转向稳健价值投资...
[来源：2024投资策略.pdf]

**主要变化**：
1. 风险偏好从激进转向稳健
2. 行业配置更加均衡
...
```

## 技术特性

### 1. 文档分块

- **分块大小**：1000 字符
- **重叠部分**：200 字符
- **分割器**：智能中文分段（按段落、句子、标点符号）

### 2. 向量嵌入

- **模型**：Google Gemini embedding-001
- **维度**：768 维向量
- **支持语言**：中文、英文

### 3. 支持的文档格式

- ✅ TXT（纯文本）
- ✅ PDF（使用 PyPDFLoader）
- ✅ DOCX（使用 Docx2txtLoader）
- ✅ DOC（自动转换）

### 4. 性能优化

- **持久化存储**：向量数据库自动持久化
- **增量索引**：只需添加新文档，无需重建整个索引
- **快速检索**：毫秒级相似度搜索

## 最佳实践

### 1. 文档命名

建议使用有意义的文件名，便于追溯来源：
```
✅ 2024Q1投资策略报告_张三.pdf
✅ 监管政策解读_20240101.docx
❌ 文档1.pdf
❌ 新建文档.txt
```

### 2. 文档质量

- 确保文档内容清晰、结构化
- 避免过多无关信息
- PDF 文档建议使用 OCR 处理后上传

### 3. 查询优化

**好的查询**：
```
✅ "AgentDesk 的知识管理功能如何使用？"
✅ "2024年科技板块投资策略"
✅ "监管对量化交易的最新要求"
```

**不好的查询**：
```
❌ "功能"（过于宽泛）
❌ "怎么办"（缺少上下文）
```

### 4. 结果数量

- **一般查询**：k=5（推荐）
- **精准查询**：k=3
- **全面检索**：k=10

## 故障排除

### 问题 1：文档上传失败

**原因**：
- 文件格式不支持
- 文件损坏
- 文件过大

**解决**：
- 检查文件格式（仅支持 TXT、PDF、DOCX）
- 尝试重新生成文档
- 分割大文件后上传

### 问题 2：搜索结果不准确

**原因**：
- 查询语句不清晰
- 知识库文档不足
- 相关文档未上传

**解决**：
- 优化查询语句，使用完整问题
- 补充相关文档到知识库
- 增加搜索结果数量（增大 k 值）

### 问题 3：向量数据库错误

**原因**：
- ChromaDB 未正确初始化
- 存储空间不足

**解决**：
```bash
# 检查数据库目录
ls -la ./chroma_db/

# 重建向量数据库（谨慎使用，会删除所有数据）
rm -rf ./chroma_db/
```

## 未来增强

计划添加的功能：

- [ ] 文档版本管理
- [ ] 知识图谱可视化
- [ ] 多模态检索（图片、表格）
- [ ] 自动摘要和标签
- [ ] 文档相似度聚类
- [ ] 播客生成（基于 NotebookLM）

## 示例代码

### Python 客户端

```python
import requests

# 添加文档
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/knowledge/add',
        files={'file': f}
    )
    print(response.json())

# 搜索知识库
response = requests.post(
    'http://localhost:8000/api/knowledge/search',
    data={'query': 'AgentDesk功能', 'k': 5}
)
results = response.json()
for item in results['results']:
    print(f"内容: {item['content'][:100]}...")
    print(f"来源: {item['metadata']['source']}")
    print(f"相似度: {item['similarity_score']}")
    print("---")
```

### JavaScript 客户端

```javascript
// 添加文档
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/knowledge/add', {
    method: 'POST',
    body: formData
})
.then(res => res.json())
.then(data => console.log(data));

// 搜索知识库
const params = new URLSearchParams({
    query: 'AgentDesk功能',
    k: 5
});

fetch('http://localhost:8000/api/knowledge/search', {
    method: 'POST',
    body: params
})
.then(res => res.json())
.then(data => {
    data.results.forEach(item => {
        console.log('内容:', item.content.substring(0, 100));
        console.log('来源:', item.metadata.source);
        console.log('相似度:', item.similarity_score);
    });
});
```

## 总结

AgentDesk 的知识管理功能为您提供了强大的文档智能检索能力。通过向量检索技术，您可以：

✅ 快速构建企业知识库  
✅ 实现智能问答  
✅ 进行多文档关联分析  
✅ 提升信息检索效率

配合专业的知识管理专家智能体，让您的文档管理更智能、更高效！




