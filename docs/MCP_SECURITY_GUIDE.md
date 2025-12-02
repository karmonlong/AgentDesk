# MCP 安全指南

## 当前安全问题

### ⚠️ 问题：所有 Web 用户共享服务器文件系统

当前 MCP 实现中，所有用户通过 `@MCP助手` 访问的是**同一个服务器文件系统**。

```
用户 A (浏览器) ──┐
用户 B (浏览器) ──┼──→ FastAPI Server ──→ MCP Server (文件系统)
用户 C (浏览器) ──┘                              ↓
                                        /Users/dragonxing/office-assistant/
```

## 解决方案

### 方案 1：用户工作空间隔离（推荐）

为每个用户创建独立的沙盒目录：

```python
# services/mcp_service.py
import uuid
from pathlib import Path

class MCPClientManager:
    def __init__(self):
        self.user_workspaces = {}  # user_id -> workspace_path
        self.workspace_root = Path("./user_workspaces")
        self.workspace_root.mkdir(exist_ok=True)
    
    def get_user_workspace(self, user_id: str) -> Path:
        """为用户创建隔离的工作空间"""
        if user_id not in self.user_workspaces:
            workspace = self.workspace_root / user_id
            workspace.mkdir(parents=True, exist_ok=True)
            self.user_workspaces[user_id] = workspace
        return self.user_workspaces[user_id]
    
    async def call_tool(self, user_id: str, command: str, args: List[str], 
                       tool_name: str, tool_args: Dict) -> Any:
        """带用户隔离的工具调用"""
        workspace = self.get_user_workspace(user_id)
        
        # 限制路径访问范围
        if tool_name in ["list_directory", "read_file", "get_file_info"]:
            requested_path = Path(tool_args.get("path", "."))
            
            # 确保路径在用户工作空间内
            if not requested_path.is_absolute():
                requested_path = workspace / requested_path
            
            try:
                requested_path = requested_path.resolve()
                if not requested_path.is_relative_to(workspace):
                    return {"error": "Access denied: Path outside workspace"}
            except:
                return {"error": "Invalid path"}
            
            tool_args["path"] = str(requested_path)
        
        # 调用 MCP
        return await self._call_mcp(command, args, tool_name, tool_args)
```

### 方案 2：权限白名单

只允许访问特定目录：

```python
ALLOWED_DIRECTORIES = [
    "/Users/dragonxing/office-assistant/uploads",
    "/Users/dragonxing/office-assistant/docs",
]

def is_path_allowed(path: str) -> bool:
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(allowed) for allowed in ALLOWED_DIRECTORIES)

@mcp.tool()
def list_directory(path: str) -> str:
    if not is_path_allowed(path):
        return "Error: Access denied"
    # ... 原有逻辑
```

### 方案 3：用户认证 + 会话管理

```python
# app.py
from fastapi import Depends, HTTPException, Cookie
from typing import Optional

async def get_current_user(session_id: Optional[str] = Cookie(None)) -> str:
    """从 cookie 获取当前用户 ID"""
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # 验证 session（从 Redis/数据库）
    user_id = await session_store.get(session_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    return user_id

@app.post("/api/chat")
async def chat_with_agent(
    message: str = Form(...),
    user_id: str = Depends(get_current_user)  # 👈 注入用户 ID
):
    # 传递 user_id 到 MCP 调用
    result = await multi_agent_system.chat(message, user_id=user_id)
    return result
```

### 方案 4：浏览器端 MCP（仅用于个人使用）

如果是桌面应用或个人工具，可以使用 Cursor 的 MCP 浏览器扩展：

```javascript
// 在浏览器中直接调用本地 MCP Server
const mcpClient = new MCPBrowserClient();
await mcpClient.connect('ws://localhost:8080');
const result = await mcpClient.callTool('list_directory', {path: '.'});
```

**这种方式用户访问的是自己的本地文件系统！**

## 推荐架构

### 当前（单用户/开发模式）
```
你的浏览器 → FastAPI (localhost:8000) → MCP → 你的文件系统 ✅
```

### 生产环境（多用户）
```
用户 A → FastAPI → MCP → /workspace/user_a/ 🔒
用户 B → FastAPI → MCP → /workspace/user_b/ 🔒
用户 C → FastAPI → MCP → /workspace/user_c/ 🔒
```

### 桌面应用/浏览器扩展
```
用户 A (Chrome) → MCP Browser Extension → 用户 A 的本地文件系统 ✅
用户 B (Firefox) → MCP Browser Extension → 用户 B 的本地文件系统 ✅
```

## 实施建议

1. **如果是内部工具/个人使用**：添加简单的路径白名单即可
2. **如果要公开部署**：必须实现用户认证 + 工作空间隔离
3. **如果是桌面应用**：考虑 Electron + 本地 MCP
4. **如果是 Chrome 扩展**：使用 MCP Browser Extension

## 安全检查清单

- [ ] 实现用户认证
- [ ] 为每个用户创建独立工作空间
- [ ] 验证所有文件路径（防止 path traversal）
- [ ] 限制可访问的文件类型
- [ ] 记录所有文件操作日志
- [ ] 设置文件大小限制
- [ ] 定期清理用户工作空间
- [ ] 禁止访问系统敏感目录（/etc, ~/.ssh, .env 等）




