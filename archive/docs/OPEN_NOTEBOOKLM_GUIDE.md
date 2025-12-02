# Open NotebookLM 使用指南

## 🎙️ 什么是 Open NotebookLM？

**Open NotebookLM** 是一个开源工具，可以将 PDF 文档转换为播客形式的音频内容。

### 核心功能

- 📄 **PDF 转播客**：上传 PDF 文档，自动生成播客对话
- 🎭 **双人对话**：模拟两位主持人的自然对话
- 🌍 **多语言支持**：支持 13 种语言
- 🎵 **高质量语音**：使用 MeloTTS 或 Suno Bark 进行语音合成
- 💡 **智能理解**：使用 Llama 3.3 70B 理解文档内容

## 🚀 快速开始

### 1. 获取 Fireworks AI API 密钥

Open NotebookLM 使用 Fireworks AI 提供的 Llama 3.3 70B 模型。

**步骤**：
1. 访问 [https://fireworks.ai/](https://fireworks.ai/)
2. 注册账户（免费试用额度）
3. 进入 Dashboard → API Keys
4. 创建新的 API Key
5. 复制 API Key

### 2. 配置 API 密钥

```bash
# 进入 open-notebooklm 目录
cd /Users/dragonxing/office-assistant/open-notebooklm

# 编辑 .env 文件
nano .env

# 将 your-fireworks-api-key-here 替换为您的实际 API 密钥
FIREWORKS_API_KEY=fw_xxxxxxxxxxxxxxxx
```

### 3. 启动 Open NotebookLM

**方式 1：使用启动脚本（推荐）**

```bash
cd /Users/dragonxing/office-assistant/open-notebooklm
./start.sh
```

**方式 2：手动启动**

```bash
cd /Users/dragonxing/office-assistant/open-notebooklm
export FIREWORKS_API_KEY=your-api-key-here
../venv/bin/python app.py
```

启动后，访问：http://localhost:7860

### 4. 使用 Open NotebookLM

1. **上传 PDF 文档**
   - 点击 "Upload File(s)" 按钮
   - 选择一个或多个 PDF 文件
   - 支持学术论文、报告、书籍等

2. **设置参数**（可选）
   - **Question**：指定播客讨论的特定问题
   - **Tone**：选择语气（Formal正式 / Casual随意 / Enthusiastic热情）
   - **Length**：选择长度（Short短 / Medium中 / Detailed详细）
   - **Language**：选择语言（中文、英文等13种）
   - **Advanced Audio**：使用高级语音模型（Suno Bark，效果更好但速度慢）

3. **生成播客**
   - 点击 "Generate Podcast" 按钮
   - 等待处理（通常需要 1-3 分钟）
   - 播放或下载生成的 MP3 文件

## 🎨 界面预览

```
┌──────────────────────────────────────────┐
│  Open NotebookLM                         │
│  Personalised Podcasts For All           │
├──────────────────────────────────────────┤
│  📁 Upload File(s)                       │
│     [Choose Files]                       │
│                                          │
│  🌐 URL (optional)                       │
│     [Enter URL]                          │
│                                          │
│  💭 Question (optional)                  │
│     [Enter specific question]            │
│                                          │
│  🎭 Tone: [Casual ▼]                    │
│  📏 Length: [Medium ▼]                   │
│  🌍 Language: [中文 ▼]                  │
│  🎵 ☐ Use Advanced Audio                │
│                                          │
│  [Generate Podcast]                      │
└──────────────────────────────────────────┘
```

## 📚 使用场景

### 场景 1：学习研究论文

```
上传：学术论文 PDF
设置：
  - Language: English
  - Length: Detailed
  - Tone: Formal
  
输出：专业的论文解读播客
```

### 场景 2：投资报告解读

```
上传：投资研报 PDF
设置：
  - Language: 中文
  - Length: Medium
  - Question: "这份报告的核心投资观点是什么？"
  
输出：轻松易懂的投资策略讨论
```

### 场景 3：会议纪要总结

```
上传：会议纪要 PDF
设置：
  - Language: 中文
  - Length: Short
  - Tone: Casual
  
输出：简短的会议要点播客
```

## 🔌 集成到 AgentDesk

### 方案 1：独立访问

Open NotebookLM 作为独立服务运行：

```bash
# 终端 1：启动 AgentDesk
cd /Users/dragonxing/office-assistant
make dev

# 终端 2：启动 Open NotebookLM
cd /Users/dragonxing/office-assistant/open-notebooklm
./start.sh
```

- **AgentDesk**：http://localhost:8000
- **Open NotebookLM**：http://localhost:7860

### 方案 2：在 AgentDesk 中嵌入

在 AgentDesk 的界面中添加 iframe 或链接：

```html
<!-- 在 command_center_v2.html 中添加 -->
<iframe src="http://localhost:7860" 
        width="100%" 
        height="800px" 
        frameborder="0">
</iframe>
```

### 方案 3：通过智能体市场访问

在智能体市场中添加 "播客生成器" 入口，点击后跳转到 Open NotebookLM。

## ⚙️ 高级配置

### 修改端口

编辑 `app.py`，在最后一行修改：

```python
if __name__ == "__main__":
    demo.launch(
        show_api=UI_SHOW_API,
        server_port=7860,  # 修改为其他端口
        server_name="0.0.0.0"  # 允许外部访问
    )
```

### 自定义提示词

编辑 `prompts.py` 文件，修改 `SYSTEM_PROMPT` 等常量：

```python
SYSTEM_PROMPT = """
你的自定义播客生成提示词...
"""
```

### 选择语音模型

- **MeloTTS**：速度快，质量好（推荐）
- **Suno Bark**：质量极高，但速度慢，支持更多语言

在界面中勾选 "Use Advanced Audio" 使用 Bark。

## 💡 最佳实践

### 1. 文档准备

- ✅ 使用文字清晰的 PDF
- ✅ 文档长度适中（10-50 页最佳）
- ❌ 避免扫描版 PDF（OCR 识别可能不准）
- ❌ 避免过多图表的文档

### 2. 参数设置

| 场景 | Tone | Length | Language |
|------|------|--------|----------|
| 学术论文 | Formal | Detailed | English/中文 |
| 投资报告 | Casual | Medium | 中文 |
| 新闻摘要 | Enthusiastic | Short | 中文 |
| 技术文档 | Formal | Medium | English |

### 3. 性能优化

- 首次运行会下载语音模型（约 1-2 GB）
- 使用 Advanced Audio 时生成时间更长（3-5 分钟）
- 建议在服务器上运行，配置更高的机器

## 🐛 常见问题

### Q1: 提示 "FIREWORKS_API_KEY not found"

**解决**：
```bash
# 检查 .env 文件是否存在
ls -la /Users/dragonxing/office-assistant/open-notebooklm/.env

# 确保已设置 API 密钥
cat /Users/dragonxing/office-assistant/open-notebooklm/.env
```

### Q2: 生成的音频没有声音

**原因**：语音模型下载失败或音频编码问题

**解决**：
```bash
# 清理缓存重新下载
rm -rf ~/.cache/huggingface
```

### Q3: PDF 解析失败

**原因**：PDF 格式不支持或损坏

**解决**：
- 尝试转换 PDF 为文本格式
- 使用 OCR 工具处理扫描版 PDF
- 检查 PDF 是否可以在 PDF 阅读器中正常打开

### Q4: 中文语音不自然

**解决**：
- 使用 Advanced Audio（Suno Bark）
- 在 prompts.py 中优化中文提示词
- 尝试不同的 Tone 和 Length 组合

## 📊 技术架构

```
┌─────────────────────────────────────────┐
│         Gradio Web 界面                 │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      PDF/URL 内容提取                   │
│      - pypdf (PDF解析)                  │
│      - Jina Reader (URL解析)            │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│    Llama 3.3 70B (Fireworks AI)        │
│    - 理解文档内容                       │
│    - 生成对话脚本                       │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│      文本转语音 (TTS)                   │
│      - MeloTTS (快速)                   │
│      - Suno Bark (高质量)               │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│       MP3 播客文件                      │
└─────────────────────────────────────────┘
```

## 🎯 未来计划

- [ ] 支持更多文档格式（DOCX、TXT、Markdown）
- [ ] 添加中文优化的语音模型
- [ ] 支持自定义主持人声音
- [ ] 添加背景音乐和音效
- [ ] 与 AgentDesk 深度集成
- [ ] 支持多文档批量处理

## 📚 相关资源

- **Open NotebookLM GitHub**: https://github.com/gabrielchua/open-notebooklm
- **Fireworks AI**: https://fireworks.ai/
- **MeloTTS**: https://huggingface.co/myshell-ai/MeloTTS-English
- **Suno Bark**: https://github.com/suno-ai/bark
- **Llama 3.3**: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct

## 📞 支持

如有问题，请：
1. 查看本文档的"常见问题"部分
2. 访问 GitHub 项目的 Issues
3. 联系 AgentDesk 技术支持

---

**享受您的智能播客生成体验！** 🎙️✨




