FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /data /data/chroma /app/data
COPY . .
ENV PYTHONUNBUFFERED=1
ENV RAG_DATA_DIR=/data
ENV CHROMA_PERSIST_DIR=/data/chroma
VOLUME ["/data"]
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
