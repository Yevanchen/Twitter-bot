import requests
import json
from typing import Optional, Dict, Any
from .lark_client import LarkClient

class CozeStreamClient:
    def __init__(self, coze_api_key: str, coze_bot_id: str, lark_client: Optional[LarkClient] = None):
        self.coze_api_key = coze_api_key
        self.coze_bot_id = coze_bot_id
        self.coze_api_url = "https://api.coze.com/v3/chat"
        self.current_message = []
        self.lark_client = lark_client

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
                    parsed = self.parse_sse_line(decoded_line)
                    
                    if parsed and parsed['type'] == 'data':
                        data_content = parsed['content']
                        if 'data' in data_content and 'messages' in data_content['data']:
                            for message in data_content['data']['messages']:
                                if message.get('type') == 'answer' and 'content' in message:
                                    current_content.append(message['content'])
                                    yield ''.join(current_content)
                        elif 'role' in data_content and data_content.get('role') == 'assistant':
                            if data_content.get('type') == 'answer' and 'content' in data_content:
                                current_content.append(data_content['content'])
                                yield ''.join(current_content)
                    
                    elif parsed and parsed['type'] == 'done':
                        final_content = ''.join(current_content)
                        if final_content:
                            yield final_content
                        break
                    
        except requests.RequestException as e:
            print(f"Request error: {str(e)}")
            yield {"error": f"Request error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            yield {"error": f"Unexpected error: {str(e)}"} 