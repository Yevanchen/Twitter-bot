def print_stream_response(response_text: str):
    """打印流式响应，保持输出在同一位置"""
    print("\r" + " " * 200, end="\r")  # 清除当前行
    print(response_text, end="", flush=True)

def validate_env_vars(required_vars: dict) -> list:
    """验证环境变量"""
    return [var for var, value in required_vars.items() if not value] 