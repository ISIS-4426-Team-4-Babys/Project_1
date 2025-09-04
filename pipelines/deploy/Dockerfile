FROM python:3.11-slim

WORKDIR /app

COPY pipelines/deploy/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/deploy/ .
COPY rabbitmq/rabbitmq.py ./rabbitmq.py

CMD ["python", "worker.py"]