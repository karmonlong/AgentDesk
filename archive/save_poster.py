import json
import base64
import re

try:
    with open('poster_response.json', 'r') as f:
        data = json.load(f)
    
    if data.get('success'):
        # 尝试获取 base64
        img_b64 = data.get('image_base64')
        
        # 如果直接没有，尝试从 html 中提取
        if not img_b64 and data.get('html'):
            html = data['html']
            match = re.search(r'base64,([^"]+)', html)
            if match:
                img_b64 = match.group(1)
        
        if img_b64:
            # 保存图片
            with open('agentdesk_poster.png', 'wb') as f_img:
                f_img.write(base64.b64decode(img_b64))
            print("✅ 海报已保存为: agentdesk_poster.png")
        elif data.get('url'):
            print(f"✅ 海报生成成功，链接: {data.get('url')}")
        else:
            print("⚠️ 未找到图片数据")
    else:
        print(f"❌ 生成失败: {data.get('error')}")
except Exception as e:
    print(f"❌ 处理出错: {e}")
