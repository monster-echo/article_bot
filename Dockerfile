FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# # 安装系统依赖
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     gcc \
#     python3-dev && \
#     rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 设置时区
ENV TZ=Asia/Shanghai

# 启动程序
CMD ["python", "-m", "main"]
