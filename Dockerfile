# Use lightweight Python
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependencies first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose Flask port
EXPOSE 5001

# Run Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "app:app", "--workers", "4", "--threads", "2", "--timeout", "120"]
