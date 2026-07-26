FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 将代码放在 /app/backend/ 下，保持 from backend.xxx 的导入路径
COPY . ./backend/

# 工作目录为 /app，uvicorn 从 /app 找 backend.main:app
WORKDIR /app
EXPOSE 8000

# 历史数据持久化目录
RUN mkdir -p /app/backend/data/history
VOLUME ["/app/backend/data"]

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
