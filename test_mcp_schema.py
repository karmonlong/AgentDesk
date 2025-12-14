"""
检查 MCP 工具的详细 schema，了解正确的参数格式
"""
import asyncio
import json
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from services.mcp_service import mcp_manager

load_dotenv()

async def check_tool_schemas():
    """检查工具的详细 schema"""
    command = "npx"
    args = [
        "-y",
        "@smithery/cli@latest",
        "run",
        "@aahl/mcp-aktools",
        "--key",
        "44c67169-65b8-4564-8c17-90bc6746c6e7"
    ]
    
    try:
        tools = await mcp_manager.list_tools(command, args)
        
        # 检查关键工具的 schema
        key_tools = ['stock_prices', 'stock_info', 'search', 'stock_news']
        
        for tool in tools:
            if tool['name'] in key_tools:
                print(f"\n{'='*60}")
                print(f"工具: {tool['name']}")
                print(f"描述: {tool['description']}")
                print(f"\n完整 Schema:")
                print(json.dumps(tool.get('input_schema', {}), indent=2, ensure_ascii=False))
                print('='*60)
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(check_tool_schemas())













