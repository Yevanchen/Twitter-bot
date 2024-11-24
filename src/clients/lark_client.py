import lark_oapi as lark
from lark_oapi.api.contact.v3 import *
from typing import Optional

class LarkClient:
    def __init__(self, app_id: str, app_secret: str):
        """初始化飞书客户端"""
        self.client = lark.Client.builder() \
            .app_id(app_id) \
            .app_secret(app_secret) \
            .log_level(lark.LogLevel.DEBUG) \
            .build()
        
    def verify_connection(self) -> bool:
        """验证飞书客户端连接是否成功"""
        try:
            request = BatchGetIdUserRequest.builder() \
                .user_id_type("open_id") \
                .request_body(BatchGetIdUserRequestBody.builder()
                            .emails(["xxxx@bytedance.com"])
                            .mobiles(["15000000000"])
                            .build()) \
                .build()
            
            response = self.client.contact.v3.user.batch_get_id(request)
            
            if not response.success():
                print(f"Verification failed: code={response.code}, msg={response.msg}, log_id={response.get_log_id()}")
                return False
                
            return True
            
        except Exception as e:
            print(f"Lark client connection error: {str(e)}")
            return False

    def send_message(self, content: str) -> bool:
        """发送消息"""
        try:
            # 这里可以添加发送消息的逻辑
            return True
        except Exception as e:
            print(f"Send message error: {str(e)}")
            return False 