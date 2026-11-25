FROM python:3.14.10-slim AS base

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 900 appuser && useradd -u 900 -g 900 -r appuser

WORKDIR /app/check-links

COPY . .

# - botocore vendors a stale cacert.pem that still trusts distrusted roots and is
#   flagged by vulnerability scanners. botocore prefers certifi when installed,
#   so point the vendored bundle at certifi's to keep a single, current trust store.
# - pip, setuptools and wheel are build-time only. pip vendors an old copy of
#   setuptools (pkg_resources) which is flagged by vulnerability scanners, so
#   remove them all once dependencies are installed.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && ln -sf "$(python -c 'import certifi; print(certifi.where())')" \
      "$(python -c 'import botocore, os; print(os.path.join(os.path.dirname(botocore.__file__), "cacert.pem"))')" \
 && pip uninstall -y pip setuptools wheel

ENV PYTHONPATH=/app/check-links

USER appuser
