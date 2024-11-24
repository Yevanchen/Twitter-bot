首先需要创建一个飞书机器人并获取相关配置：
在飞书开放平台创建应用
获取 App ID 和 App Secret
- app id ：cli_a7b60234b0bd100c
- app secret ：aP8wZLgrarnDu1IgziNfsg1JyoUvdnBy
开启机器人功能并获取 Verification Token
- Encrypt Key
TCMBxB57lqBrfCTD84xe0eAjmV2G4vXG
- Verification Token
ydT4MudMEmXep1bDpXBXNdyVkGIiYocL

然后需要准备 Coze API 的配置：
在 Coze 平台发布 Agent 并获取 API Key
获取 Agent ID


coze api get start
Overview
The Coze API is a professional technological interaction capability provided by the Coze platform for developers. It is dedicated to fulfilling developers' demands more efficiently and comprehensively through APIs.
Getting Started
Before you start with Coze API, you need to create API Personal Access Token. Also, build and publish a Coze bot as API.
Please redirect to Coze API Docs for more detailed instructions.
Use Cases
Non-streaming Chat
Streaming Chat
Chat with Chat History
Request
shell
Copy
curl --location --request POST 'https://api.coze.com/v3/chat?conversation_id=7374752000116113452' \
--header 'Authorization: Bearer pat_OYDacMzM3WyOWV3Dtj2bHRMymzxP****' \
--header 'Content-Type: application/json' \
--data-raw '{
    "bot_id": "7348293334459318316",
    "user_id": "123456789",
    "stream": false,
    "auto_save_history":true,
    "additional_messages":[
        {
            "role":"user",
            "content":"What a nice day",
            "content_type":"text"
        }
    ]
}'
Response
json
Copy
{
    "data": {
        "id": "7384454522229407762",
        "conversation_id": "7384452690904137746",
        "bot_id": "7384443635783794695",
        "created_at": 1719327307,
        "last_error": {
            "code": 0,
            "msg": ""
        },
        "status": "in_progress"
    },
    "code": 0,
    "msg": ""
}
