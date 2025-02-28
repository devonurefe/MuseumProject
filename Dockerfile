# Use a slim Python image as the base
FROM python:3.10.11-slim

# Install necessary system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-nld \
    libtesseract-dev \
    poppler-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose a fixed port
EXPOSE 10000

# Run the application using Gunicorn with configurable options
CMD ["gunicorn", "--bind", "0.0.0.0:10000", \
    "--workers", "2", \
    "--timeout", "760", \
    "--max-requests", "500", \
    "--worker-class", "gthread", \
    "--threads", "2", \
    "app:app"]
