FROM python:3.9-slim

WORKDIR /app

# 实时显示 Python 日志，不缓冲
ENV PYTHONUNBUFFERED=1

# 安装依赖
RUN pip install --no-cache-dir requests python-dotenv

# 拷贝代码
COPY . .

# 确保挂载点存在
RUN mkdir -p /app/public

# 暴露记忆服务器端口（默认 8080）
EXPOSE 8080

# 默认启动天气同步；如需启动记忆服务器，覆盖 CMD 为 python server.py
CMD ["python", "main.py"]
