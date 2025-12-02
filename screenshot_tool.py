#!/usr/bin/env python3
"""
浏览器截图工具
用于自动截图 AgentDesk 界面
"""

import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
from datetime import datetime

# 截图保存目录
SCREENSHOT_DIR = Path("docs/images/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# 应用地址
BASE_URL = "http://localhost:8000"

async def take_screenshot(page, url, filename, description="", wait_selector=None):
    """截图并保存"""
    print(f"📸 正在截图: {description or filename}")
    try:
        # 使用 load 而不是 networkidle，更宽松
        await page.goto(url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(3000)  # 等待页面完全加载
        
        # 如果指定了选择器，等待该元素
        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=10000)
            except:
                pass  # 如果选择器不存在，继续截图
        
        screenshot_path = SCREENSHOT_DIR / filename
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"✅ 已保存: {screenshot_path}")
        return str(screenshot_path)
    except Exception as e:
        print(f"❌ 截图失败 {filename}: {e}")
        return None

async def screenshot_homepage(page):
    """首页截图"""
    return await take_screenshot(
        page, 
        BASE_URL,
        "01-homepage.png",
        "首页 - 传统界面"
    )

async def screenshot_chat(page):
    """对话界面截图"""
    return await take_screenshot(
        page,
        f"{BASE_URL}/chat",
        "02-chat-interface.png",
        "对话界面"
    )

async def screenshot_command_center(page):
    """指挥中心截图"""
    return await take_screenshot(
        page,
        f"{BASE_URL}/command",
        "03-command-center.png",
        "指挥中心 - 可视化工作流"
    )

async def screenshot_agents_list(page):
    """智能体列表截图（如果有）"""
    # 先访问指挥中心，然后可能需要交互
    await page.goto(f"{BASE_URL}/command", wait_until="networkidle")
    await page.wait_for_timeout(3000)
    
    screenshot_path = SCREENSHOT_DIR / "04-agents-list.png"
    await page.screenshot(path=str(screenshot_path), full_page=True)
    print(f"✅ 已保存: {screenshot_path}")
    return str(screenshot_path)

async def main():
    """主函数"""
    print("🚀 开始截图 AgentDesk 界面...")
    print(f"📁 截图保存目录: {SCREENSHOT_DIR.absolute()}")
    print(f"🌐 应用地址: {BASE_URL}")
    print("-" * 60)
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2  # 高分辨率
        )
        page = await context.new_page()
        
        screenshots = []
        
        # 截图列表
        try:
            # 1. 首页
            path = await screenshot_homepage(page)
            if path:
                screenshots.append(path)
            
            # 2. 对话界面
            path = await screenshot_chat(page)
            if path:
                screenshots.append(path)
            
            # 3. 指挥中心
            path = await screenshot_command_center(page)
            if path:
                screenshots.append(path)
            
            # 4. 智能体列表（在指挥中心中）
            path = await screenshot_agents_list(page)
            if path:
                screenshots.append(path)
                
        except Exception as e:
            print(f"❌ 截图过程出错: {e}")
        finally:
            await browser.close()
    
    print("-" * 60)
    print(f"✅ 截图完成！共生成 {len(screenshots)} 张截图")
    print(f"📁 保存位置: {SCREENSHOT_DIR.absolute()}")
    
    # 生成截图列表
    if screenshots:
        list_file = SCREENSHOT_DIR / "screenshots_list.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            f.write("# AgentDesk 截图列表\n\n")
            for i, path in enumerate(screenshots, 1):
                filename = os.path.basename(path)
                f.write(f"{i}. {filename}\n")
        print(f"📝 截图列表已保存: {list_file}")

if __name__ == "__main__":
    asyncio.run(main())

