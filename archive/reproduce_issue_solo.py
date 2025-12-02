import requests
import json

def test_translate():
    url = "http://localhost:8000/api/chat"
    payload = {"message": "@翻译专家 请帮我翻译 Hello World"}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    print("Testing translation...")
    response = requests.post(url, data=payload)
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_translate()
