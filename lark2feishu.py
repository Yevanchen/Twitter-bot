import requests
import json
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

class CozeStreamClient:
    def __init__(self, coze_api_key: str, coze_bot_id: str):
        self.coze_api_key = coze_api_key
        self.coze_bot_id = coze_bot_id
        self.coze_api_url = "https://api.coze.com/v3/chat"
        self.current_message = []

    def parse_sse_line(self, line: str) -> Optional[Dict]:
        """解析 SSE 格式的行"""
        if not line:
            return None
            
        if line.startswith('data:'):
            data = line[5:].strip()
            if data == '[DONE]':
                return {'type': 'done'}
            try:
                return {'type': 'data', 'content': json.loads(data)}
            except json.JSONDecodeError:
                return None
                
        if line.startswith('event:'):
            return {'type': 'event', 'content': line[6:].strip()}
            
        return None

    def stream_chat(self, user_message: str, user_id: str = "123456789"):
        """发起流式对话请求并处理响应"""
        headers = {
            'Authorization': f'Bearer {self.coze_api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            "bot_id": self.coze_bot_id,
            "user_id": user_id,
            "stream": True,
            "auto_save_history": False,
            "additional_messages": [
                {
                    "role": "user",
                    "content": user_message,
                    "content_type": "text"
                }
            ]
        }

        try:
            response = requests.post(
                self.coze_api_url,
                headers=headers,
                json=data,
                stream=True
            )
            
            if response.status_code != 200:
                error_content = response.json()
                print(f"HTTP Error: {response.status_code}")
                print(f"Error details: {error_content}")
                yield error_content
                return

            current_content = []
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    print(f"Debug - Received line: {decoded_line}")  # 调试信息
                    
                    parsed = self.parse_sse_line(decoded_line)
                    print(f"Debug - Parsed result: {parsed}")  # 调试信息
                    
                    if parsed and parsed['type'] == 'data':
                        data_content = parsed['content']
                        # 处理消息完成事件
                        if 'data' in data_content and 'messages' in data_content['data']:
                            for message in data_content['data']['messages']:
                                if message.get('type') == 'answer' and 'content' in message:
                                    print(f"Debug - Found message content: {message['content']}")  # 调试信息
                                    current_content.append(message['content'])
                                    yield ''.join(current_content)
                        # 处理消息增量更新
                        elif 'role' in data_content and data_content.get('role') == 'assistant':
                            if data_content.get('type') == 'answer' and 'content' in data_content:
                                print(f"Debug - Found delta content: {data_content['content']}")  # 调试信息
                                current_content.append(data_content['content'])
                                yield ''.join(current_content)
                    
                    elif parsed and parsed['type'] == 'done':
                        final_content = ''.join(current_content)
                        print(f"Debug - Final content: {final_content}")  # 调试信息
                        if final_content:  # 确保有内容才yield
                            yield final_content
                        break
                    
        except requests.RequestException as e:
            print(f"Request error: {str(e)}")
            yield {"error": f"Request error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            yield {"error": f"Unexpected error: {str(e)}"}

def print_stream_response(response_text: str):
    """打印流式响应，保持输出在同一位置"""
    print("\r" + " " * 200, end="\r")  # 清除当前行，增加清除的长度
    print(response_text, end="", flush=True)

def main():
    # 从环境变量获取配置
    COZE_API_KEY = os.getenv('COZE_API_KEY')
    COZE_BOT_ID = os.getenv('COZE_BOT_ID')

    # 验证必要的环境变量
    if not all([COZE_API_KEY, COZE_BOT_ID]):
        print("Error: Missing required environment variables. Please check your .env file.")
        return

    client = CozeStreamClient(COZE_API_KEY, COZE_BOT_ID)

    message = "2024 11.24 dify 在推特上发生了什么"
    print(f"\n发送流式消息: {message}\n")
    
    # 用于存储完整的响应
    full_response = ""
    response_count = 0  # 添加计数器
    
    try:
        for response in client.stream_chat(message):
            response_count += 1  # 计数
            print(f"Debug - Response #{response_count}: {response}")  # 调试信息
            
            if isinstance(response, dict) and "error" in response:
                print(f"\nError: {response['error']}")
            else:
                full_response = response
                print_stream_response(full_response)
    except KeyboardInterrupt:
        print("\n\n用户中断了对话")
    except Exception as e:
        print(f"\n\n发生错误: {str(e)}")
    finally:
        # 完成后打印换行
        print("\n\n完整响应已完成")
        print(f"\n最终响应:\n{full_response}")
        print(f"Debug - Total responses received: {response_count}")  # 调试信息

if __name__ == "__main__":
    main()
