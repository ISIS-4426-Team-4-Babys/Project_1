FROM python:3.11-slim

WORKDIR /app

COPY pipelines/preprocess/requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/preprocess/ .
COPY rabbitmq/rabbitmq.py ./rabbitmq.py

CMD ["python", "worker.py"]