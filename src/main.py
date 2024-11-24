from dotenv import load_dotenv
import os
from src.clients.lark_client import LarkClient
from src.clients.coze_client import CozeStreamClient
from src.utils.helpers import print_stream_response, validate_env_vars

# 加载环境变量
load_dotenv()

def main():
    # 从环境变量获取配置
    LARK_APP_ID = os.getenv('LARK_APP_ID')
    LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
    COZE_API_KEY = os.getenv('COZE_API_KEY')
    COZE_BOT_ID = os.getenv('COZE_BOT_ID')

    # 验证必要的环境变量
    required_vars = {
        'LARK_APP_ID': LARK_APP_ID,
        'LARK_APP_SECRET': LARK_APP_SECRET,
        'COZE_API_KEY': COZE_API_KEY,
        'COZE_BOT_ID': COZE_BOT_ID
    }

    missing_vars = validate_env_vars(required_vars)
    if missing_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
        return

    # 初始化飞书客户端
    print("正在初始化飞书客户端...")
    lark_client = LarkClient(LARK_APP_ID, LARK_APP_SECRET)
    
    # 验证飞书连接
    if not lark_client.verify_connection():
        print("飞书客户端连接失败，请检查配置")
        return
    
    print("飞书客户端连接成功")

    # 初始化Coze客户端
    client = CozeStreamClient(COZE_API_KEY, COZE_BOT_ID, lark_client)

    message = "2024 11.24 dify 在推特上发生了什么"
    print(f"\n发送流式消息: {message}\n")
    
    # 用于存储完整的响应
    full_response = ""
    response_count = 0
    
    try:
        for response in client.stream_chat(message):
            response_count += 1
            
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
        print("\n\n完整响应已完成")
        print(f"\n最终响应:\n{full_response}")
        print(f"Debug - Total responses received: {response_count}")

if __name__ == "__main__":
    main() 