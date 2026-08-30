FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/packages/core

COPY packages/core /app/packages/core
RUN pip install --upgrade pip \
    && pip install /app/packages/core \
    && groupadd --system app \
    && useradd --system --gid app --create-home app

USER app

EXPOSE 8000
