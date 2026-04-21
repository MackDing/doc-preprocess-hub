FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY app ./app

CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=INFO", "-Q", "queue.postproc"]
