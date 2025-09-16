FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pipelines/preprocess/requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/preprocess/ .
COPY rabbitmq/rabbitmq.py ./rabbitmq.py

CMD ["python", "worker.py"]