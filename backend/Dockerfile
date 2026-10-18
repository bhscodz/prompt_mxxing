# File: backend/Dockerfile
# Description: Dockerfile for FastAPI Python Backend with PyTorch and Asyncpg

FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["python", "run_backend.py"]

