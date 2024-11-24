from flask import Flask, request, jsonify
import sys
import os
from dotenv import load_dotenv
import lark_oapi as lark
import time
import logging

# 使用绝对导入
from src.clients.lark_client import LarkClient
from src.clients.coze_client import CozeStreamClient
from src.utils.helpers import print_stream_response, validate_env_vars

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 初始化客户端
LARK_APP_ID = os.getenv('LARK_APP_ID')
LARK_APP_SECRET = os.getenv('LARK_APP_SECRET')
COZE_API_KEY = os.getenv('COZE_API_KEY')
COZE_BOT_ID = os.getenv('COZE_BOT_ID')

lark_client = None
coze_client = None

# 验证必要的环境变量
required_vars = {
    'LARK_APP_ID': LARK_APP_ID,
    'LARK_APP_SECRET': LARK_APP_SECRET,
    'COZE_API_KEY': COZE_API_KEY,
    'COZE_BOT_ID': COZE_BOT_ID,
    'ENCRYPT_KEY': os.getenv('ENCRYPT_KEY'),
    'VERIFICATION_TOKEN': os.getenv('VERIFICATION_TOKEN')
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    sys.exit(1)

# 初始化事件处理器
handler = lark.EventDispatcherHandler.builder(
    required_vars['ENCRYPT_KEY'],
    required_vars['VERIFICATION_TOKEN'],
    lark.LogLevel.DEBUG
).build()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_clients():
    global lark_client, coze_client
    # 初始化飞书客户端
    lark_client = LarkClient(LARK_APP_ID, LARK_APP_SECRET)
    # 初始化Coze客户端
    coze_client = CozeStreamClient(COZE_API_KEY, COZE_BOT_ID, lark_client)

@app.route("/webhook/lark", methods=["POST"])
def lark_webhook():
    # 获取飞书的事件推送
    event_data = request.json
    
    # 处理飞书的验证请求
    if "challenge" in event_data:
        return jsonify({"challenge": event_data["challenge"]})
    
    # 处理消息事件
    try:
        if event_data.get("type") == "message":
            message = event_data["event"]["message"]["content"]
            # 调用 Coze 处理消息
            response = coze_client.stream_chat(message)
            # 处理响应...
            return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error processing message: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/webhook/event", methods=["POST"])
def event_webhook():
    try:
        logger.info("Received webhook event")
        event_data = request.get_json()
        logger.info(f"Event data: {event_data}")
        
        if event_data and event_data.get("type") == "url_verification":
            logger.info("Processing URL verification")
            return jsonify({"challenge": event_data.get("challenge")})
            
        # 处理加密请求
        if event_data and "encrypt" in event_data:
            # 使用 lark SDK 的事件处理器直接处理加密数据
            response = handler.do(event_data)
            return jsonify(response)
            
        # 处理其他事件
        response = handler.do(event_data)
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/health", methods=["GET"])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "env": {
            "FLASK_ENV": os.getenv("FLASK_ENV", "production"),
            "LARK_APP_ID": bool(LARK_APP_ID),  # 只返回是否存在，不返回具体值
            "COZE_BOT_ID": bool(COZE_BOT_ID)
        }
    })

if __name__ == "__main__":
    init_clients()
    app.run(host="0.0.0.0", port=3000) 