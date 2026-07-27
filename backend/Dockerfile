# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# 系统依赖（精简版）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 包
COPY --from=builder /install /usr/local

# 应用代码
COPY . .

# 创建数据目录
RUN mkdir -p data/{certificates,thumbnails,backups,logs,config,workspace}

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
