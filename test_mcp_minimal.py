import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 设置环境变量，确保能找到 tools 目录
os.environ["PYTHONPATH"] = os.getcwd()

async def run():
    # 1. 定义服务器参数
    # 我们直接运行 tools/mcp_server_fs.py
    server_script = os.path.join("tools", "mcp_server_fs.py")
    
    print(f"Testing MCP Server at: {server_script}")
    
    server_params = StdioServerParameters(
        command=sys.executable, # 使用当前的 python 解释器
        args=[server_script],
        env=os.environ
    )

    print("Connecting...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # 2. 列出工具
                print("\n--- Listing Tools ---")
                result = await session.list_tools()
                for tool in result.tools:
                    print(f"Tool: {tool.name}")
                    print(f"  Desc: {tool.description}")
                
                # 3. 测试调用 'list_directory'
                print("\n--- Calling tool: list_directory ---")
                call_result = await session.call_tool("list_directory", arguments={"path": "."})
                print("Result:")
                # mcp 1.0+ call_tool 返回的是 CallToolResult 对象，包含 content 列表
                for content in call_result.content:
                    if content.type == "text":
                        # 只打印前 200 个字符避免刷屏
                        print(content.text[:200] + "..." if len(content.text) > 200 else content.text)

                print("\n✅ MCP Server Minimal Test Passed!")

    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run())
