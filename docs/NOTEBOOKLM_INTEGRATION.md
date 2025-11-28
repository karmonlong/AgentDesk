# NotebookLM 集成使用指南

## 🎯 集成方式

AgentDesk 采用 **VS Code 风格的插件集成方式**，将 Open NotebookLM 作为可订阅的智能体插件。

---

## 📝 使用步骤

### 1. 启动 Open NotebookLM 服务

在使用前，需要先启动 Open NotebookLM 服务：

```bash
# 终端 1：启动 Open NotebookLM
cd /Users/dragonxing/office-assistant/open-notebooklm
export FIREWORKS_API_KEY=fw_3ZLottgs5YMxkBg3rJdDLbTH
../venv/bin/python app.py

# 或使用启动脚本（需要先配置 .env）
./start.sh
```

**预期输出**：
```
* Running on local URL:  http://0.0.0.0:7860
```

### 2. 在 AgentDesk 中订阅 NotebookLM

1. 访问 **http://localhost:8000**
2. 点击左侧活动栏的 **🏪 智能体市场** 图标
3. 滚动到底部找到 **🎙️ NotebookLM**
4. 点击 **"获取"** 按钮订阅

### 3. 使用 NotebookLM

订阅后，NotebookLM 图标会自动出现在左侧活动栏中（在搜索图标下方）。

**两种使用方式**：

#### 方式 A：侧边栏集成 ⭐ **推荐**

1. 点击活动栏中的 **🎙️ NotebookLM 图标**
2. 侧边栏会展开显示 NotebookLM 界面
3. 直接在侧边栏中使用 NotebookLM 的所有功能

**优势**：
- ✅ 无需切换窗口
- ✅ 保持工作流连贯性
- ✅ 可以同时查看文件和使用 NotebookLM

#### 方式 B：新窗口打开

1. 在智能体市场的 NotebookLM 详情页
2. 点击 **"新窗口打开"** 按钮
3. 在独立浏览器标签页中使用

---

## 🎨 界面布局

### VS Code 风格的活动栏

```
┌────────────────────────────────────────┐
│ AgentDesk                              │
├────┬───────────────────────────────────┤
│ 📁 │ 资源管理器                        │
│    ├───────────────────────────────────┤
│ 💼 │ 业务场景                          │
│    │                                   │
│ 🏪 │ 智能体市场                        │
│    │                                   │
│ 🔍 │ 搜索                              │
│    │                                   │
│ 🎙️ │ ← NotebookLM (订阅后出现)       │
│    │                                   │
│    │                                   │
│ ⚙️ │ 设置                              │
└────┴───────────────────────────────────┘
```

### NotebookLM 侧边栏面板

```
┌──────────────────────────────────────┐
│ 🎙️ NotebookLM              [折叠 ←] │
├──────────────────────────────────────┤
│                                      │
│  [Open NotebookLM 界面嵌入在这里]   │
│                                      │
│  • 上传 PDF 文档                     │
│  • 设置语言和语气                    │
│  • 生成播客音频                      │
│  • 下载 MP3 文件                     │
│                                      │
└──────────────────────────────────────┘
```

---

## ⚙️ 技术实现

### 集成架构

```
┌─────────────────────────────────────────┐
│         AgentDesk (主应用)              │
│         Port: 8000                      │
│                                         │
│  ┌────────────────────────────────┐   │
│  │  活动栏 (Activity Bar)         │   │
│  │  ├─ 资源管理器                 │   │
│  │  ├─ 智能体市场                 │   │
│  │  └─ NotebookLM (动态添加) ────┼───┼─→ 订阅后出现
│  └────────────────────────────────┘   │
│                                         │
│  ┌────────────────────────────────┐   │
│  │  侧边栏面板                    │   │
│  │  ├─ panel-explorer             │   │
│  │  ├─ panel-market               │   │
│  │  └─ panel-notebooklm ──────────┼───┼─→ iframe 嵌入
│  └────────────────────────────────┘   │
└─────────────────────────────────────────┘
                    │
                    │ iframe 
                    │ src="http://localhost:7860"
                    ▼
┌─────────────────────────────────────────┐
│    Open NotebookLM (独立服务)          │
│    Port: 7860                           │
│                                         │
│    • PDF 文档分析                       │
│    • 对话脚本生成                       │
│    • 语音合成                           │
└─────────────────────────────────────────┘
```

### 关键代码

**智能体配置** (marketAgents 数组):
```javascript
{
    name: 'NotebookLM',
    desc: 'PDF 文档深度分析与播客生成',
    icon: 'fas fa-podcast',
    color: '#E91E63',
    subscribed: false,
    isExternal: true,
    activityBarId: 'activity-notebooklm',  // 活动栏图标 ID
    panelId: 'notebooklm',                 // 侧边栏面板 ID
    externalUrl: 'http://localhost:7860'
}
```

**动态添加到活动栏**:
```javascript
function addToActivityBar(agent) {
    const container = document.getElementById('subscribed-agents-bar');
    const activityItem = document.createElement('div');
    activityItem.id = agent.activityBarId;
    activityItem.className = 'activity-item';
    activityItem.onclick = () => switchSidebar(agent.panelId);
    activityItem.innerHTML = `<i class="${agent.icon}"></i>`;
    container.appendChild(activityItem);
}
```

---

## 🔧 配置和故障排除

### 确保服务正常运行

检查 Open NotebookLM 是否启动：
```bash
curl -I http://localhost:7860
```

预期返回：
```
HTTP/1.1 200 OK
```

### 常见问题

#### Q1: NotebookLM 图标没有出现

**原因**：未订阅或服务未启动

**解决**：
1. 在智能体市场中订阅 NotebookLM
2. 检查 Open NotebookLM 服务是否运行
3. 刷新页面

#### Q2: 侧边栏显示"正在启动"

**原因**：Open NotebookLM 服务未启动

**解决**：
```bash
cd /Users/dragonxing/office-assistant/open-notebooklm
export FIREWORKS_API_KEY=fw_3ZLottgs5YMxkBg3rJdDLbTH
../venv/bin/python app.py
```

#### Q3: iframe 无法加载

**原因**：
- 端口冲突
- 浏览器跨域限制

**解决**：
1. 检查 7860 端口是否被占用
2. 尝试"新窗口打开"方式
3. 检查浏览器控制台错误信息

---

## 🎯 使用场景

### 场景 1：投资研报转播客

**工作流**：
1. 在资源管理器上传 PDF 研报
2. 点击 NotebookLM 图标打开侧边栏
3. 在 NotebookLM 中上传同一份 PDF
4. 设置：中文 / 随意语气 / 中等长度
5. 生成播客并下载
6. 在通勤路上收听

### 场景 2：多文档分析

**工作流**：
1. 上传多份相关文档到 AgentDesk
2. 使用知识管理专家进行向量检索
3. 切换到 NotebookLM
4. 将关键文档转换为播客
5. 结合文字分析和音频播客，全面理解内容

### 场景 3：快速内容消费

**工作流**：
1. 收到大量 PDF 文档
2. 批量上传到 NotebookLM
3. 生成多个播客音频
4. 在工作间隙或休息时收听
5. 快速掌握文档核心内容

---

## 💡 最佳实践

### 1. 文档准备

**✅ 适合转播客的文档**：
- 投资研报
- 行业分析
- 学术论文
- 长篇文章
- 会议纪要

**❌ 不适合的文档**：
- 纯数据表格
- 扫描版 PDF
- 图片为主的文档

### 2. 参数设置

| 文档类型 | 语言 | 语气 | 长度 |
|---------|------|------|------|
| 投资研报 | 中文 | 轻松随意 | 中等 |
| 学术论文 | 英文 | 正式 | 详细 |
| 新闻摘要 | 中文 | 热情 | 简短 |
| 技术文档 | 英文 | 正式 | 中等 |

### 3. 工作流建议

**高效模式**：
```
上传文档 → AgentDesk 分析关键点 → NotebookLM 生成播客 → 边听边review
```

**深度模式**：
```
多文档上传 → 知识库检索对比 → 提取核心文档 → 生成播客 → 精读 + 精听
```

---

## 🚀 未来增强

计划添加的功能：

- [ ] 直接从资源管理器右键发送到 NotebookLM
- [ ] 播客文件自动保存到 AgentDesk
- [ ] 支持播放列表管理
- [ ] 与知识库深度集成
- [ ] 多语言字幕生成
- [ ] 播客内容搜索

---

## 📚 相关文档

- [AgentDesk 文档分析指南](./DOCUMENT_ANALYSIS_GUIDE.md)
- [知识管理功能指南](./KNOWLEDGE_MANAGEMENT.md)
- [Open NotebookLM GitHub](https://github.com/gabrielchua/open-notebooklm)

---

**享受 NotebookLM 集成带来的文档分析和播客生成体验！** 🎙️✨




