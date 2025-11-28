#!/usr/bin/env python3
"""
测试带文档的翻译任务
"""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_translate_with_doc():
    """测试翻译文档"""
    print("=" * 60)
    print("测试: 翻译任务 + 文档上传")
    print("=" * 60)
    
    try:
        # 创建测试文档
        test_content = """
科技金融创新策略研究

摘要：本文探讨了科技与金融融合的创新路径。

主要内容：
1. 金融科技的发展现状
2. 创新策略分析
3. 未来趋势预测
"""
        
        files = {
            'document': ('test_doc.txt', test_content.encode('utf-8'), 'text/plain')
        }
        data = {
            'message': '@翻译专家 将以下内容翻译成英文'
        }
        
        print("📤 发送请求...")
        print(f"消息: {data['message']}")
        print(f"文档: test_doc.txt ({len(test_content)} 字符)")
        
        start_time = time.time()
        
        response = requests.post(
            f"{BASE_URL}/api/chat",
            data=data,
            files=files,
            timeout=90  # 90秒超时
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n⏱️  耗时: {elapsed:.2f}秒")
        print(f"📊 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ 成功!")
                print(f"\n智能体: {result.get('agent', {}).get('name')}")
                print(f"\n响应内容:")
                print("-" * 60)
                print(result.get('response', '')[:500])
                if len(result.get('response', '')) > 500:
                    print("...")
                print("-" * 60)
            else:
                print(f"❌ 失败: {result.get('error')}")
        else:
            print(f"❌ HTTP 错误")
            print(f"响应: {response.text[:500]}")
            
    except requests.Timeout:
        print(f"❌ 请求超时（>90秒）")
    except Exception as e:
        print(f"❌ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_translate_with_doc()
