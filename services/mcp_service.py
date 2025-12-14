import asyncio
import os
import json
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from langchain_core.tools import Tool

class MCPClientManager:
    """
    管理 MCP (Model Context Protocol) 连接
    支持连接到本地 Stdio Server 或远程 SSE Server (暂未实现)
    """
    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.connections: Dict[str, Any] = {} # Store connection params/handles
        self.active_tools: Dict[str, List[Dict]] = {}

    async def connect_stdio(self, connection_id: str, command: str, args: List[str], env: Optional[Dict] = None):
        """
        连接到基于 Stdio 的 MCP Server
        """
        print(f"[MCP] Connecting to stdio server: {command} {' '.join(args)}")
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **(env or {})}
        )

        try:
            # 我们需要保持连接上下文，这里使用 mcp 提供的上下文管理器比较 tricky，
            # 因为我们需要长期保持连接。
            # 我们需要手动管理 transport 和 session。
            
            # 注意：mcp 库的设计通常是用于上下文管理器。
            # 为了长期保持，我们需要创建 task 或者以某种方式持有 transport。
            # 这里的实现是一个简化版，每次调用可能需要重新连接，或者我们需要由外部控制生命周期。
            # 为了演示，我们先实现一个 "一次性获取工具列表" 的功能，
            # 真正的长期连接需要更复杂的异步管理。
            
            # 实际上，为了让 Agent 能随时调用，我们需要一个后台运行的 Session。
            # 让我们尝试启动一个后台 Task 来维持连接。
            
            # 暂时：为了简单起见，我们假设连接是“按需”的，或者由上层调用者维持。
            # 但 Agent 需要 Tool 对象，Tool 对象调用时需要 Session。
            
            pass 

        except Exception as e:
            print(f"[MCP] Connection failed: {e}")
            raise e

    async def list_tools(self, command: str, args: List[str]) -> List[Dict]:
        """
        连接 Server 并列出可用工具 (临时连接)
        """
        # 优先尝试 HTTP (streamable) 方式 —— 适配 Smithery 提供的 HTTP MCP 服务
        http_url = self._build_http_url(command, args)
        if http_url:
            tools = []
            async with streamablehttp_client(http_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    for tool in result.tools:
                        tools.append({
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema
                        })
            return tools

        # 回退到 stdio 方式
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=os.environ
        )
        
        tools = []
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List tools
                result = await session.list_tools()
                for tool in result.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    })
        return tools

    async def call_tool(self, command: str, args: List[str], tool_name: str, tool_args: Dict) -> Any:
        """
        连接 Server 并调用工具 (临时连接)
        """
        # 优先尝试 HTTP (streamable) 方式
        http_url = self._build_http_url(command, args)
        if http_url:
            async with streamablehttp_client(http_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    return result

        # 回退到 stdio 方式
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=os.environ
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Call tool
                result = await session.call_tool(tool_name, arguments=tool_args)
                return result

    def _build_http_url(self, command: str, args: List[str]) -> Optional[str]:
        """
        如果配置里包含 Smithery 的 aktools（通过 npx 调用），构造 HTTP URL。
        """
        # 只对 aktools 的 npx 方式做特殊处理
        if command != "npx":
            return None
        if "@aahl/mcp-aktools" not in args:
            return None

        # 从参数中提取 key，例如: ["-y", "@smithery/cli@latest", "run", "@aahl/mcp-aktools", "--key", "<KEY>"]
        api_key = None
        if "--key" in args:
            idx = args.index("--key")
            if idx + 1 < len(args):
                api_key = args[idx + 1]

        if not api_key:
            return None

        base_url = "https://server.smithery.ai/@aahl/mcp-aktools/mcp"
        return f"{base_url}?{urlencode({'api_key': api_key})}"

# 全局实例
mcp_manager = MCPClientManager()
