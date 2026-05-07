FROM python:3.14-bookworm

ENV PYTHONUNBUFFERED=1 \
PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen

COPY . .
EXPOSE 8000
