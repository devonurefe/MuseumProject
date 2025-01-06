FROM python:3.10.11-slim

# Sistem bağımlılıklarını yükle
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-nld \
    libtesseract-dev \
    poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Çalışma dizinini ayarla
WORKDIR /app

# Python bağımlılıklarını yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Uygulama için port tanımla
EXPOSE 5000

# Uygulamayı başlat
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
