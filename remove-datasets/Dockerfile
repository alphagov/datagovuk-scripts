FROM python:3.11.13-slim AS base

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 900 appuser && useradd -u 900 -g 900 -r appuser

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

USER appuser
