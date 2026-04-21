# NOTE: this Dockerfile is a scaffold. Once MinerU is wired in, switch to
# a CUDA base image (e.g. nvidia/cuda:12.4.0-runtime-ubuntu22.04) and bake
# the model weights into the image per docs/deployment.md.
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

COPY app ./app

CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=INFO", "-Q", "queue.mineru"]
