# Simple Dockerfile for PostgreSQL-only deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Set work directory
WORKDIR /app

# Install system dependencies (PostgreSQL only)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gcc \
        python3-dev \
        libpq-dev \
        netcat-openbsd \
        iputils-ping \
        dnsutils \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools && \
    pip install --prefer-binary --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy startup script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Create directories
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 8080

# Run startup script
CMD ["/app/start.sh"]
