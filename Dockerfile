FROM python:3.11-slim AS base

WORKDIR /app

COPY check-links/ ./check-links/
RUN pip install --no-cache-dir psycopg2-binary requests boto3 pytest

ENV PYTHONPATH=/app/check-links
