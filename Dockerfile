FROM python:3.10.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    tesseract-ocr-nld \
    libtesseract-dev \
    poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=10000
EXPOSE $PORT

# Memory limit ve timeout ayarları eklendi
CMD gunicorn --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 760 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --log-level debug \
    --worker-class gthread \
    --threads 4 \
    app:app