# 使用 Python 3.8 作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装 poetry
RUN pip install poetry==1.7.1

# 配置 poetry - 禁用虚拟环境创建
RUN poetry config virtualenvs.create false

# 复制项目文件
COPY pyproject.toml poetry.lock ./

# 安装依赖
RUN poetry install --no-interaction --no-ansi

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 