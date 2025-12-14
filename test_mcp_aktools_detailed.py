"""
详细测试 akshare MCP 服务器的多个工具
"""
import asyncio
import json
import sys
import os
from dotenv import load_dotenv

sys.path.append(os.getcwd())
from services.mcp_service import mcp_manager

load_dotenv()

async def test_multiple_tools():
    """测试多个工具"""
    print("=" * 60)
    print("详细测试 akshare MCP 服务器")
    print("=" * 60)
    
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
        # 获取工具列表
        tools = await mcp_manager.list_tools(command, args)
        print(f"\n✅ 连接到 MCP 服务器，共 {len(tools)} 个工具\n")
        
        # 测试 1: 获取当前时间
        print("[测试 1] 获取当前时间和交易日信息...")
        try:
            result = await mcp_manager.call_tool(command, args, "get_current_time", {})
            if hasattr(result, 'content') and result.content:
                print("✅ 成功获取时间信息")
                for item in result.content:
                    if hasattr(item, 'text'):
                        print(f"   {item.text[:200]}")
        except Exception as e:
            print(f"❌ 失败: {e}")
        
        # 测试 2: 获取股票基本信息
        print("\n[测试 2] 获取股票基本信息 (000001 平安银行)...")
        try:
            result = await mcp_manager.call_tool(command, args, "stock_info", {
                "symbol": "000001",
                "market": "A"
            })
            if hasattr(result, 'content') and result.content:
                print("✅ 成功获取股票信息")
                for item in result.content:
                    if hasattr(item, 'text'):
                        print(f"   {item.text[:300]}")
        except Exception as e:
            print(f"❌ 失败: {e}")
        
        # 测试 3: 获取股票价格数据 - 尝试多种格式
        print("\n[测试 3] 获取股票历史价格 (尝试不同格式)...")
        
        # 尝试格式 1: 使用完整股票代码格式 (000001.SZ)
        test_formats = [
            {"symbol": "000001.SZ", "market": "A", "period": "1d", "limit": 10},
            {"symbol": "000001", "market": "A", "period": "1d", "limit": 10},
            {"symbol": "600000", "market": "A", "period": "1d", "limit": 10},  # 上交所股票
            {"symbol": "600000.SH", "market": "A", "period": "1d", "limit": 10},
        ]
        
        success = False
        for i, params in enumerate(test_formats, 1):
            try:
                print(f"   尝试格式 {i}: symbol={params['symbol']}, market={params['market']}")
                result = await mcp_manager.call_tool(command, args, "stock_prices", params)
                if hasattr(result, 'content') and result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            text = item.text
                            if "Not Found" not in text and "Error" not in text:
                                print(f"   ✅ 成功！使用格式: symbol={params['symbol']}")
                                lines = text.split('\n')[:5]
                                print(f"   前5行数据:\n   " + "\n   ".join(lines))
                                if len(text.split('\n')) > 5:
                                    print(f"   ... (共 {len(text.split(chr(10)))} 行)")
                                success = True
                                break
                            else:
                                print(f"   ❌ 返回: {text[:100]}")
                if success:
                    break
            except Exception as e:
                print(f"   ❌ 格式 {i} 失败: {str(e)[:100]}")
        
        if not success:
            print("   ⚠️  所有格式都未成功，可能需要检查数据源或参数")
        
        # 测试 4: 获取股票新闻
        print("\n[测试 4] 获取股票相关新闻 (000001, 最近3条)...")
        try:
            result = await mcp_manager.call_tool(command, args, "stock_news", {
                "symbol": "000001",
                "limit": 3
            })
            if hasattr(result, 'content') and result.content:
                print("✅ 成功获取新闻")
                for item in result.content:
                    if hasattr(item, 'text'):
                        text = item.text
                        # 显示前200字符
                        print(f"   {text[:200]}...")
        except Exception as e:
            print(f"❌ 失败: {e}")
        
        # 测试 5: 搜索股票 - 尝试不同关键词
        print("\n[测试 5] 搜索股票 (尝试不同关键词)...")
        
        search_keywords = [
            {"keyword": "平安银行", "market": "A"},
            {"keyword": "平安", "market": "A"},
            {"keyword": "招商银行", "market": "A"},
            {"keyword": "600036", "market": "A"},  # 尝试股票代码
        ]
        
        success = False
        for i, params in enumerate(search_keywords, 1):
            try:
                print(f"   尝试关键词 {i}: {params['keyword']}")
                result = await mcp_manager.call_tool(command, args, "search", params)
                if hasattr(result, 'content') and result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            text = item.text
                            if "Not Found" not in text and "Error" not in text and len(text.strip()) > 0:
                                print(f"   ✅ 成功！关键词: {params['keyword']}")
                                lines = text.split('\n')[:10]
                                print(f"   前10条结果:\n   " + "\n   ".join(lines))
                                success = True
                                break
                            else:
                                print(f"   ❌ 返回: {text[:100] if text else '空结果'}")
                if success:
                    break
            except Exception as e:
                print(f"   ❌ 关键词 {i} 失败: {str(e)[:100]}")
        
        if not success:
            print("   ⚠️  搜索功能可能需要特定格式或数据源暂时不可用")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n[清理] 关闭 MCP 连接...")
        await mcp_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_multiple_tools())

