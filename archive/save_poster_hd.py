import json
import base64
import re

try:
    with open('poster_hd_response.json', 'r') as f:
        data = json.load(f)
    
    if data.get('success'):
        img_b64 = data.get('image_base64')
        if not img_b64 and data.get('data') and isinstance(data['data'], dict):
            img_b64 = data['data'].get('image_base64')
            
        if not img_b64 and data.get('html'):
            html = data['html']
            match = re.search(r'base64,([^"]+)', html)
            if match:
                img_b64 = match.group(1)
        
        if img_b64:
            with open('agentdesk_poster_hd.png', 'wb') as f_img:
                f_img.write(base64.b64decode(img_b64))
            print("✅ 高清海报已保存为: agentdesk_poster_hd.png")
        elif data.get('url'):
            print(f"✅ 海报生成成功，链接: {data.get('url')}")
        else:
            print(f"⚠️ 未找到图片数据: {data}")
    else:
        print(f"❌ 生成失败: {data.get('error')}")
except Exception as e:
    print(f"❌ 处理出错: {e}")
