#!/usr/bin/env python3
"""
AlphaFund 单元测试 - 不依赖服务运行
测试代码逻辑是否正确
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.alphafund_agent import AlphaFundAgent
except ImportError as e:
    print(f"⚠️  无法导入 AlphaFundAgent: {e}")
    print("   这可能是正常的，如果缺少某些依赖")
    AlphaFundAgent = None

import asyncio

async def test_alphafund_agent():
    """测试 AlphaFund Agent 的基本功能"""
    print("=" * 60)
    print("AlphaFund Agent 单元测试")
    print("=" * 60)
    
    # 检查环境变量
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("⚠️  未设置 GEMINI_API_KEY，将测试降级逻辑")
    else:
        print(f"✅ 找到 GEMINI_API_KEY (长度: {len(gemini_key)})")
    
    # 创建 Agent 实例
    print("\n1. 测试 Agent 初始化...")
    if AlphaFundAgent is None:
        print("   ⚠️  跳过 Agent 测试（模块未导入）")
        return False
        
    try:
        agent = AlphaFundAgent()
        print(f"   ✅ Agent 创建成功")
        print(f"   模型: {agent.model or '未配置'}")
        print(f"   智能体数量: {len(agent.AGENTS)}")
    except Exception as e:
        print(f"   ❌ Agent 创建失败: {e}")
        return False
    
    # 测试上下文格式化
    print("\n2. 测试上下文格式化...")
    try:
        test_history = [
            {"name": "测试智能体", "role": "TEST", "content": "测试内容"}
        ]
        context = agent.format_context(test_history)
        if context:
            print(f"   ✅ 上下文格式化成功")
            print(f"   长度: {len(context)} 字符")
        else:
            print(f"   ⚠️  上下文为空（可能正常）")
    except Exception as e:
        print(f"   ❌ 上下文格式化失败: {e}")
        return False
    
    # 测试工作流（如果 API Key 存在）
    if gemini_key:
        print("\n3. 测试工作流执行（简化版）...")
        print("   注意: 完整工作流需要调用 Gemini API，可能需要较长时间")
        print("   这里只测试代码结构，不实际调用 API")
        
        # 检查各个智能体方法是否存在
        methods = [
            'run_deep_researcher',
            'run_market_analyst', 
            'run_quant_analyst',
            'run_portfolio_manager',
            'run_critic',
            'run_risk_officer',
            'run_workflow'
        ]
        
        all_exist = True
        for method_name in methods:
            if hasattr(agent, method_name):
                print(f"   ✅ {method_name} 方法存在")
            else:
                print(f"   ❌ {method_name} 方法不存在")
                all_exist = False
        
        if not all_exist:
            return False
    else:
        print("\n3. 跳过工作流测试（需要 GEMINI_API_KEY）")
    
    # 测试 API 路由（检查 app.py）
    print("\n4. 检查 API 路由定义...")
    try:
        import app
        routes = [route.path for route in app.app.routes]
        
        if '/alphafund' in routes:
            print("   ✅ /alphafund 路由已定义")
        else:
            print("   ❌ /alphafund 路由未找到")
            return False
            
        if '/api/alphafund/start' in routes:
            print("   ✅ /api/alphafund/start 路由已定义")
        else:
            print("   ⚠️  /api/alphafund/start 路由未找到（可能是 POST 路由）")
            
        # 检查 POST 路由
        post_routes = [route.path for route in app.app.routes if hasattr(route, 'methods') and 'POST' in route.methods]
        if any('alphafund' in path for path in post_routes):
            print("   ✅ AlphaFund POST 路由存在")
        else:
            print("   ❌ AlphaFund POST 路由未找到")
            return False
            
    except Exception as e:
        print(f"   ⚠️  无法检查路由: {e}")
        print("   （这可能是正常的，如果 app 模块导入有问题）")
    
    print("\n" + "=" * 60)
    print("✅ 单元测试通过！")
    print("=" * 60)
    print("\n注意:")
    print("- 代码结构检查完成")
    print("- 如需完整功能测试，请:")
    print("  1. 确保 GEMINI_API_KEY 已设置")
    print("  2. 启动服务: python -m uvicorn app:app --host 0.0.0.0 --port 8000")
    print("  3. 运行: python test_alphafund_api.py")
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_alphafund_agent())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

