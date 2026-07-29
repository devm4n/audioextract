FROM python:3.14-bookworm

ENV PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml ./

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN uv sync

COPY . .
EXPOSE 8000
