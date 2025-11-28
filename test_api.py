#!/usr/bin/env python3
"""
测试指挥中心 API 接口连通性
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_api_agents():
    """测试智能体列表接口"""
    print("=" * 60)
    print("测试 1: 获取智能体列表 (/api/agents)")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/api/agents", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功! 共有 {len(data.get('agents', []))} 个智能体")
            for agent in data.get('agents', [])[:3]:
                print(f"  - {agent.get('name')}: {agent.get('role')}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()


def test_api_chat_simple():
    """测试简单对话接口（无文档）"""
    print("=" * 60)
    print("测试 2: 简单对话 (/api/chat)")
    print("=" * 60)
    
    try:
        data = {
            "message": "你好，请做个自我介绍"
        }
        
        print("发送消息:", data["message"])
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            data=data,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        print(f"状态码: {response.status_code}")
        print(f"耗时: {elapsed:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 成功!")
                print(f"智能体: {result.get('agent', {}).get('name')}")
                print(f"响应预览: {result.get('response', '')[:200]}...")
            else:
                print(f"❌ 失败: {result.get('error')}")
        else:
            print(f"❌ 失败: {response.text[:500]}")
    except requests.Timeout:
        print(f"❌ 请求超时（>60秒）")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()


def test_api_chat_with_file():
    """测试带文档的对话接口"""
    print("=" * 60)
    print("测试 3: 带文档对话 (/api/chat)")
    print("=" * 60)
    
    try:
        # 创建一个临时测试文件
        test_content = "这是一个测试文档。\n主要内容：测试文档上传功能。\n结论：系统运行正常。"
        
        files = {
            'document': ('test.txt', test_content, 'text/plain')
        }
        data = {
            'message': '请总结这份文档'
        }
        
        print("发送消息:", data["message"])
        print("附带文档: test.txt")
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            data=data,
            files=files,
            timeout=60
        )
        
        elapsed = time.time() - start_time
        print(f"状态码: {response.status_code}")
        print(f"耗时: {elapsed:.2f}秒")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 成功!")
                print(f"智能体: {result.get('agent', {}).get('name')}")
                print(f"响应预览: {result.get('response', '')[:200]}...")
            else:
                print(f"❌ 失败: {result.get('error')}")
        else:
            print(f"❌ 失败: {response.text[:500]}")
    except requests.Timeout:
        print(f"❌ 请求超时（>60秒）")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print()


def main():
    print("\n🧪 开始测试指挥中心 API 接口\n")
    
    # 运行测试
    test_api_agents()
    test_api_chat_simple()
    test_api_chat_with_file()
    
    print("=" * 60)
    print("测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
