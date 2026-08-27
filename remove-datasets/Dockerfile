FROM 3.11.16-alpine3.23

RUN apk update && apk upgrade && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 900 appuser && useradd -u 900 -g 900 -r appuser

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install msgpack==1.2.1
RUN pip install setuptools 78.1.1
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app

USER appuser
