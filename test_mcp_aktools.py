"""
测试 akshare MCP 服务器是否正常工作
"""
import asyncio
import json
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from services.mcp_service import mcp_manager

load_dotenv()

async def test_mcp_aktools():
    """测试 akshare MCP 服务器"""
    print("=" * 60)
    print("测试 akshare MCP 服务器")
    print("=" * 60)
    
    # MCP 服务器配置
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
        # 步骤 1: 列出可用工具
        print("\n[步骤 1] 连接到 MCP 服务器并列出可用工具...")
        tools = await mcp_manager.list_tools(command, args)
        
        print(f"\n✅ 成功连接到 MCP 服务器！")
        print(f"📋 可用工具数量: {len(tools)}")
        print("\n可用工具列表:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i}. {tool['name']}")
            print(f"     描述: {tool['description'][:80]}...")
            if 'input_schema' in tool:
                print(f"     输入参数: {list(tool['input_schema'].get('properties', {}).keys())}")
            print()
        
        # 步骤 2: 测试调用一个工具（查询股票数据）
        if tools:
            print("\n[步骤 2] 测试调用工具...")
            
            # 查找股票相关的工具
            stock_tool = None
            for tool in tools:
                if 'stock' in tool['name'].lower() or '实时' in tool['description'] or '行情' in tool['description']:
                    stock_tool = tool
                    break
            
            if not stock_tool:
                # 如果没有找到，使用第一个工具
                stock_tool = tools[0]
            
            print(f"选择工具: {stock_tool['name']}")
            print(f"工具描述: {stock_tool['description']}")
            
            # 根据工具名称决定调用参数
            tool_name = stock_tool['name']
            tool_args = {}
            
            # 根据工具名称和输入 schema 设置正确的参数
            if 'input_schema' in stock_tool and 'properties' in stock_tool['input_schema']:
                props = stock_tool['input_schema']['properties']
                required = stock_tool['input_schema'].get('required', [])
                
                # 根据工具类型设置参数
                if tool_name == 'stock_info':
                    tool_args = {
                        "symbol": "000001",  # 股票代码
                        "market": "A"  # A股市场
                    }
                elif tool_name == 'stock_prices':
                    tool_args = {
                        "symbol": "000001",
                        "market": "A",
                        "period": "1d",
                        "limit": 10
                    }
                elif tool_name == 'get_current_time':
                    tool_args = {}  # 无参数
                elif tool_name == 'stock_news':
                    tool_args = {
                        "symbol": "000001",
                        "limit": 5
                    }
                else:
                    # 对于其他工具，使用 schema 中的默认值或第一个枚举值
                    for key in required:
                        if key in props:
                            prop = props[key]
                            if 'default' in prop:
                                tool_args[key] = prop['default']
                            elif 'enum' in prop and prop['enum']:
                                tool_args[key] = prop['enum'][0]
                            elif key == 'symbol':
                                tool_args[key] = "000001"
                            elif key == 'market':
                                tool_args[key] = "A"
                            elif key == 'limit':
                                tool_args[key] = 5
            else:
                # 如果没有 schema，使用默认参数
                if 'stock' in tool_name.lower():
                    tool_args = {"symbol": "000001", "market": "A"}
                else:
                    tool_args = {}
            
            print(f"\n调用参数: {json.dumps(tool_args, ensure_ascii=False, indent=2)}")
            
            try:
                result = await mcp_manager.call_tool(command, args, tool_name, tool_args)
                print(f"\n✅ 工具调用成功！")
                print(f"结果类型: {type(result)}")
                
                # 格式化输出结果
                if hasattr(result, 'content'):
                    if isinstance(result.content, list):
                        for item in result.content:
                            if hasattr(item, 'text'):
                                print(f"\n结果内容:\n{item.text[:500]}...")
                            else:
                                print(f"\n结果项: {item}")
                    else:
                        print(f"\n结果内容:\n{str(result.content)[:500]}...")
                else:
                    print(f"\n结果: {str(result)[:500]}...")
                    
            except Exception as e:
                print(f"\n❌ 工具调用失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("\n⚠️  没有可用工具")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n[清理] 关闭 MCP 连接...")
        await mcp_manager.cleanup()
        print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(test_mcp_aktools())

