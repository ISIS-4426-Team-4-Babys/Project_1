FROM python:3.11-slim

WORKDIR /app

COPY pipelines/deploy/templates/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY pipelines/deploy/templates/ .

CMD ["python", "backend.py"] 