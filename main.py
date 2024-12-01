from datetime import datetime
from pydantic import BaseModel
import requests
import json
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from typing import Optional, Dict
from dotenv import load_dotenv
import os
from fastapi import FastAPI, HTTPException
import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    CreateMessageRequest,
    CreateMessageRequestBody,
    CreateMessageResponse,
)

# 加载环境变量·
load_dotenv()
app = FastAPI()


class MessageRequest(BaseModel):
    message: str


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

        if line.startswith("data:"):
            data = line[5:].strip()
            if data == "[DONE]":
                return {"type": "done"}
            try:
                return {"type": "data", "content": json.loads(data)}
            except json.JSONDecodeError:
                return None

        if line.startswith("event:"):
            return {"type": "event", "content": line[6:].strip()}

        return None

    def get_stream_chat(self, user_message: str, user_id: str = "123456789"):
        """发起流式对话请求并处理响应"""
        headers = {
            "Authorization": f"Bearer {self.coze_api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "bot_id": self.coze_bot_id,
            "user_id": user_id,
            "stream": True,
            "auto_save_history": False,
            "additional_messages": [
                {"role": "user", "content": user_message, "content_type": "text"}
            ],
        }

        try:
            response = requests.post(
                self.coze_api_url, headers=headers, json=data, stream=True
            )

            if response.status_code != 200:
                error_content = response.json()
                print(f"HTTP Error: {response.status_code}")
                print(f"Error details: {error_content}")
                return error_content

            current_content = []
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    parsed = self.parse_sse_line(decoded_line)
                    print(f"Debug - Parsed result: {parsed}")  # 调试信息

                    if parsed and parsed["type"] == "data":
                        data_content = parsed["content"]
                        # 处理消息完成事件
                        if (
                            "data" in data_content
                            and "messages" in data_content["data"]
                        ):
                            for message in data_content["data"]["messages"]:
                                if (
                                    message.get("type") == "answer"
                                    and "content" in message
                                ):
                                    print(
                                        f"Debug - Found message content: {message['content']}"
                                    )  # 调试信息
                                    current_content.append(message["content"])
                        # 处理消息增量更新
                        elif (
                            "role" in data_content
                            and data_content.get("role") == "assistant"
                        ):
                            if (
                                data_content.get("type") == "answer"
                                and "content" in data_content
                            ):
                                print(
                                    f"Debug - Found delta content: {data_content['content']}"
                                )  # 调试信息
                                if "".join(current_content) != data_content["content"]:
                                    current_content.append(data_content["content"])

                    elif parsed and parsed["type"] == "done":
                        final_content = "".join(current_content)
                        print(f"Debug - Final content: {final_content}")  # 调试信息
                        break
            return current_content
        except requests.RequestException as e:
            print(f"Request error: {str(e)}")
            return {"error": f"Request error: {str(e)}"}
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}


def get_coze_response(message: str) -> str:
    # 从环境变量获取配置
    COZE_API_KEY = os.getenv("COZE_API_KEY")
    COZE_BOT_ID = os.getenv("COZE_BOT_ID")

    # 验证必要的环境变量
    if not all([COZE_API_KEY, COZE_BOT_ID]):
        print(
            "Error: Missing required environment variables. Please check your .env file."
        )
        return

    client = CozeStreamClient(COZE_API_KEY, COZE_BOT_ID)
    # 用于存储完整的响应
    try:
        full_response = client.get_stream_chat(message)
        return "".join(full_response)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/send_message/")
def send_message(request: MessageRequest):
    message = request.message
    FEISHU_BOT_APP_ID = "cli_a7b60234b0bd100c"
    FEISHU_AK = "aP8wZLgrarnDu1IgziNfsg1JyoUvdnBy"
    GROUP_CHAT_ID = "oc_b9100ee0ef5535f682b1f6e4932cad99"

    # 创建client
    feishu_client = (
        lark.Client.builder()
        .app_id(FEISHU_BOT_APP_ID)
        .app_secret(FEISHU_AK)
        .log_level(lark.LogLevel.DEBUG)
        .build()
    )
    response_dict = {
        "zh_cn": {
            "title": "",
            "content": [
                [{"tag": "md", "text": get_coze_response(message)}],
            ],
        }
    }
    # 构造请求对象
    request: CreateMessageRequest = (
        CreateMessageRequest.builder()
        .receive_id_type("chat_id")
        .request_body(
            CreateMessageRequestBody.builder()
            .receive_id(GROUP_CHAT_ID)
            .msg_type("post")
            .content(json.dumps(response_dict))
            .build()
        )
        .build()
    )

    # 发起请求
    response: CreateMessageResponse = feishu_client.im.v1.message.create(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, \
                msg: {response.msg}, log_id: {response.get_log_id()}, \
                    resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}"
        )
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return {"message": "success"}


def scheduled_task():
    message = f"{datetime.now().strftime('%Y %m %d')} dify发生了什么"
    send_message(MessageRequest(message=message))


scheduler = BlockingScheduler()
scheduler.add_job(
    scheduled_task, CronTrigger(hour=8, minute=0)
)  # 每天早上 8 点触发一次
scheduler.start()


# 启动应用
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=1,
        loop="auto",
        reload=True  # 开发环境可以启用，生产环境建议关闭
    )
