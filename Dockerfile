# Dockerfile
FROM python:3.11-slim

# Install ffmpeg and required OS packages
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ffmpeg \
    build-essential \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create app dir
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose internal port
EXPOSE 5001

# Create a non-root user (optional but recommended)
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Use gunicorn for production
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:5001", "app:app"]
