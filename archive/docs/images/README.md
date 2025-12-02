# AgentDesk 截图资源

本目录包含 AgentDesk 系统的界面截图，用于文档和演示。

## 📸 截图列表

### 核心界面

1. **01-homepage.png** - 首页（传统界面）
   - 展示文档上传和处理功能
   - 适合展示基础功能

2. **02-chat-interface.png** - 对话界面
   - 展示多智能体对话交互
   - 适合展示智能体协作

3. **03-command-center.png** - 指挥中心
   - 展示可视化工作流监控
   - 适合展示系统架构和创新点

4. **04-agents-list.png** - 智能体列表
   - 展示智能体团队
   - 适合展示多智能体系统

## 🛠️ 截图工具

使用 `screenshot_tool.py` 可以自动截图：

```bash
# 确保应用正在运行
make run  # 或 make dev

# 运行截图工具
python3 screenshot_tool.py
```

截图会自动保存到 `docs/images/screenshots/` 目录。

## 📝 在文档中使用

在 Markdown 文档中引用截图：

```markdown
![首页界面](images/screenshots/01-homepage.png)

![对话界面](images/screenshots/02-chat-interface.png)

![指挥中心](images/screenshots/03-command-center.png)
```

## 🔄 更新截图

当界面有更新时，重新运行截图工具即可：

```bash
python3 screenshot_tool.py
```

## 📋 截图规范

- **分辨率**：1920x1080（可调整）
- **格式**：PNG
- **质量**：高分辨率（device_scale_factor=2）
- **全页面**：full_page=True（包含滚动内容）


