#!/usr/bin/env python3
"""
测试 AlphaFund API 接口
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_alphafund_page():
    """测试工作区页面是否可访问"""
    print("=" * 60)
    print("测试 1: AlphaFund 工作区页面")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/alphafund", timeout=5)
        if response.status_code == 200:
            print("✅ 页面加载成功")
            print(f"   状态码: {response.status_code}")
            print(f"   内容长度: {len(response.text)} 字节")
            if "AlphaFund" in response.text:
                print("   ✅ 页面包含 'AlphaFund' 内容")
            else:
                print("   ⚠️  页面可能缺少预期内容")
            return True
        else:
            print(f"❌ 页面加载失败，状态码: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务已启动")
        print("   启动命令: python -m uvicorn app:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_alphafund_api():
    """测试投研工作流 API"""
    print("\n" + "=" * 60)
    print("测试 2: AlphaFund 工作流 API")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "基础测试（无深度研究）",
            "topic": "英伟达",
            "deep_research": False
        },
        {
            "name": "深度研究测试",
            "topic": "新能源",
            "deep_research": True
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试用例 {i}: {test_case['name']} ---")
        print(f"   主题: {test_case['topic']}")
        print(f"   深度研究: {test_case['deep_research']}")
        
        try:
            form_data = {
                "topic": test_case["topic"],
                "deep_research": str(test_case["deep_research"]).lower()
            }
            
            print("   正在发送请求...")
            start_time = time.time()
            
            response = requests.post(
                f"{BASE_URL}/api/alphafund/start",
                data=form_data,
                timeout=120  # 工作流可能需要较长时间
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("success"):
                    print(f"   ✅ API 调用成功 (耗时: {elapsed_time:.2f}秒)")
                    print(f"   状态: {data.get('status', 'unknown')}")
                    
                    report = data.get("report", {})
                    if report:
                        print(f"   ✅ 返回报告数据")
                        print(f"      主题: {report.get('topic', 'N/A')}")
                        print(f"      标题: {report.get('title', 'N/A')}")
                        print(f"      状态: {report.get('status', 'N/A')}")
                        
                        # 检查各个智能体的输出
                        if report.get("deepResearchAnalysis"):
                            print(f"      ✅ 深度研究分析: 已生成")
                        if report.get("marketAnalysis"):
                            print(f"      ✅ 市场分析: 已生成")
                        if report.get("quantAnalysis"):
                            print(f"      ✅ 量化分析: 已生成")
                        if report.get("investmentThesis"):
                            print(f"      ✅ 投资备忘录: 已生成")
                        if report.get("critiqueAnalysis"):
                            print(f"      ✅ 评审分析: 已生成")
                        if report.get("riskAssessment"):
                            risk = report["riskAssessment"]
                            print(f"      ✅ 风险审查: 评分 {risk.get('score', 'N/A')}, 通过: {risk.get('approved', 'N/A')}")
                        
                        if report.get("agentContext"):
                            print(f"      ✅ 智能体上下文: {len(report['agentContext'])} 条消息")
                    else:
                        print("   ⚠️  报告数据为空")
                    
                    results.append(True)
                else:
                    print(f"   ❌ API 返回失败")
                    print(f"   错误: {data.get('error', '未知错误')}")
                    results.append(False)
            else:
                print(f"   ❌ HTTP 错误，状态码: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('error', '未知错误')}")
                except:
                    print(f"   响应内容: {response.text[:200]}")
                results.append(False)
                
        except requests.exceptions.Timeout:
            print(f"   ❌ 请求超时（超过 120 秒）")
            results.append(False)
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 无法连接到服务器")
            results.append(False)
        except Exception as e:
            print(f"   ❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    return all(results)

def main():
    print("\n" + "=" * 60)
    print("AlphaFund API 接口测试")
    print("=" * 60)
    print(f"测试目标: {BASE_URL}")
    print()
    
    # 检查服务是否运行
    try:
        requests.get(f"{BASE_URL}/", timeout=2)
        print("✅ 服务正在运行\n")
    except:
        print("❌ 服务未运行，请先启动服务:")
        print("   python -m uvicorn app:app --host 0.0.0.0 --port 8000\n")
        sys.exit(1)
    
    # 运行测试
    test1_result = test_alphafund_page()
    test2_result = test_alphafund_api()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"页面访问测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"API 功能测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败，请检查上述错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()










