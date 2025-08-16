FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (ffmpeg + build tools)
RUN apt-get update && apt-get install -y ffmpeg gcc libffi-dev && rm -rf /var/lib/apt/lists/*

# Copy app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir flask gunicorn pydub requests

# Expose port 8080 (not 5001!)
EXPOSE 8080

# Start Gunicorn on port 8080
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "api:app"]
