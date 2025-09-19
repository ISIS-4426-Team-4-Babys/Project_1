FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY workers/deploy/templates/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from transformers import AutoModel; AutoModel.from_pretrained('BAAI/bge-reranker-v2-m3')"

RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2', model_kwargs={'device':'cpu'})"

COPY workers/deploy/templates/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]