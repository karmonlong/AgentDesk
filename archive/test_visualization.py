#!/usr/bin/env python3
"""
测试数据可视化专家功能
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_visualization_agent():
    """测试数据可视化专家"""
    print("=" * 80)
    print("🎨 测试数据可视化专家")
    print("=" * 80)
    
    test_cases = [
        {
            "message": "@数据可视化专家 帮我画一个今年基金收益率的柱状图",
            "desc": "基础柱状图测试"
        },
        {
            "message": "@数据可视化专家 生成一个显示月度销售数据的折线图",
            "desc": "折线图测试"
        },
        {
            "message": "画一个饼图展示不同基金类型的占比",
            "desc": "关键词触发测试（不使用@）"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i}: {test['desc']} ---")
        print(f"消息: {test['message']}")
        
        try:
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/api/chat",
                data={"message": test['message']},
                timeout=60
            )
            
            elapsed = time.time() - start_time
            print(f"⏱️  耗时: {elapsed:.2f}秒")
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    agent_name = result.get('agent', {}).get('name', '未知')
                    response_text = result.get('response', '')
                    
                    print(f"✅ 成功!")
                    print(f"📢 智能体: {agent_name}")
                    
                    # 检查是否包含 HTML 代码块
                    if '```html' in response_text:
                        print(f"🎉 检测到 HTML 代码块!")
                        
                        # 提取 HTML 代码块数量
                        html_count = response_text.count('```html')
                        print(f"📊 HTML 代码块数量: {html_count}")
                        
                        # 显示响应预览
                        preview = response_text[:300].replace('\n', ' ')
                        print(f"📄 响应预览: {preview}...")
                        
                        # 检查常见的图表库引用
                        if 'chart.js' in response_text.lower():
                            print(f"   └─ 使用了 Chart.js ✓")
                        if 'echarts' in response_text.lower():
                            print(f"   └─ 使用了 ECharts ✓")
                    else:
                        print(f"⚠️  未检测到 HTML 代码块")
                        print(f"📄 响应内容: {response_text[:200]}...")
                else:
                    print(f"❌ 请求失败: {result.get('error', '未知错误')}")
            else:
                print(f"❌ HTTP 错误: {response.status_code}")
                print(f"   {response.text[:200]}")
                
        except requests.Timeout:
            print(f"❌ 请求超时（>60秒）")
        except Exception as e:
            print(f"❌ 异常: {e}")
        
        print()
    
    print("=" * 80)
    print("✅ 数据可视化测试完成!")
    print("=" * 80)


def check_agent_registered():
    """检查数据可视化专家是否已注册"""
    print("\n🔍 检查智能体注册状态...\n")
    
    try:
        response = requests.get(f"{BASE_URL}/api/agents", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', [])
            
            print(f"📋 系统中共有 {len(agents)} 个智能体:\n")
            
            found_viz = False
            for agent in agents:
                name = agent.get('name', '')
                role = agent.get('role', '')
                emoji = agent.get('emoji', '')
                
                if '可视化' in name or 'visualization' in name.lower():
                    print(f"✅ {emoji} {name} ({role}) ⭐")
                    found_viz = True
                else:
                    print(f"   {emoji} {name} ({role})")
            
            print()
            
            if found_viz:
                print("🎉 数据可视化专家已成功注册!\n")
                return True
            else:
                print("⚠️  未找到数据可视化专家\n")
                return False
        else:
            print(f"❌ 无法获取智能体列表: {response.status_code}\n")
            return False
            
    except Exception as e:
        print(f"❌ 错误: {e}\n")
        return False


def main():
    print("\n" + "=" * 80)
    print("🚀 AgentDesk - 数据可视化专家测试")
    print("=" * 80)
    
    # 1. 检查智能体是否注册
    if not check_agent_registered():
        print("⚠️  数据可视化专家未注册，测试无法继续")
        return
    
    # 2. 测试可视化功能
    time.sleep(1)
    test_visualization_agent()
    
    print("\n✨ 全部测试完成! 请在浏览器中查看实际渲染效果。")
    print("   访问: http://localhost:8000/templates/command_center_v2.html\n")


if __name__ == "__main__":
    main()




