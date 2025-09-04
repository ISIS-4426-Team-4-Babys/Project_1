FROM python:3.11-slim

WORKDIR /app

COPY barriers/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY barriers/ .
COPY rabbitmq/rabbitmq.py ./rabbitmq.py

CMD ["python", "worker.py"]