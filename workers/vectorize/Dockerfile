FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY workers/vectorize/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2', model_kwargs={'device':'cpu'})"

COPY workers/vectorize/ .
COPY rabbitmq/rabbitmq.py ./rabbitmq.py

CMD ["python", "worker.py"]