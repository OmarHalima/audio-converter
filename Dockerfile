# Dockerfile
FROM python:3.10-slim

# Install system deps (ffmpeg + wget). Keep image small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python deps and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .

# Create folders (redundant with app, but nice to ensure permissions)
RUN mkdir -p /app/uploads /app/converted

# Expose the port EasyPanel expects (8080)
EXPOSE 8080

# Use Gunicorn to run the app: module is app.py, Flask instance is `app`
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--workers", "4", "--timeout", "120"]
