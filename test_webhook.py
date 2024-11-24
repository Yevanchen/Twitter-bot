import requests
import json
import time

def test_webhook():
    url = "https://twitterbot.hkg1.zeabur.app/webhook/event"
    
    # 测试 URL 验证（不带加密）
    verification_data = {
        "challenge": "ajls384kdj1234",
        "type": "url_verification",
        "token": "ydT4MudMEmXep1bDpXBXNdyVkGIiYocL"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Lark-Verification/1.0'  # 添加 User-Agent
    }
    
    try:
        # 1. 首先测试服务是否在线
        print("\n1. 测试服务是否在线:")
        try:
            health_check = requests.get(url.replace("/webhook/event", "/health"))
            print(f"Health check status: {health_check.status_code}")
        except Exception as e:
            print(f"Health check failed: {str(e)}")

        # 2. 测试不带加密的验证
        print("\n2. 测试不带加密的验证:")
        print(f"请求 URL: {url}")
        print(f"请求头: {headers}")
        print(f"请求体: {json.dumps(verification_data, indent=2)}")
        
        # 添加重试逻辑
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url, 
                    json=verification_data, 
                    headers=headers,
                    timeout=10  # 设置超时
                )
                print(f"\n尝试 #{attempt + 1}")
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                print(f"Response Body: {response.text}")
                
                if response.status_code == 200:
                    verify_webhook_response(response.text, verification_data["challenge"])
                    break
                elif response.status_code == 502:
                    print(f"收到 502 错误，等待重试...")
                    time.sleep(2)  # 等待2秒后重试
                else:
                    print(f"收到非预期的状态码")
                    break
                    
            except requests.Timeout:
                print(f"请求超时，尝试 #{attempt + 1}")
            except requests.RequestException as e:
                print(f"请求错误，尝试 #{attempt + 1}: {str(e)}")
        
        # 3. 打印 curl 命令
        print("\n3. 可以使用以下 curl 命令手动测试:")
        print(f"""
curl -v --location '{url}' \\
--header 'Content-Type: application/json' \\
--header 'User-Agent: Lark-Verification/1.0' \\
--data '{json.dumps(verification_data)}'
        """)
        
        # 4. 打印诊断信息
        print("\n4. 诊断信息:")
        try:
            dns_info = requests.get("https://twitterbot.hkg1.zeabur.app")
            print(f"DNS 解析正常，服务器响应: {dns_info.status_code}")
        except Exception as e:
            print(f"DNS 或连接问题: {str(e)}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

def verify_webhook_response(response_data, challenge):
    """验证响应是否正确"""
    try:
        response_json = json.loads(response_data)
        if response_json.get("challenge") == challenge:
            print("\n✅ 验证成功: challenge 值匹配")
            return True
        else:
            print("\n❌ 验证失败: challenge 值不匹配")
            print(f"期望的值: {challenge}")
            print(f"实际的值: {response_json.get('challenge')}")
            return False
    except json.JSONDecodeError:
        print("\n❌ 验证失败: 响应不是有效的 JSON 格式")
        return False
    except Exception as e:
        print(f"\n❌ 验证失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_webhook() 