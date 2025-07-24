# Simple Dockerfile for PostgreSQL-only deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=core.settings

# Set work directory
WORKDIR /app

# Install system dependencies (PostgreSQL only)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools && \
    pip install --prefer-binary --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# ✅ Set environment untuk sub-path
ENV FORCE_SCRIPT_NAME=/ryo-api
ENV DJANGO_SETTINGS_MODULE=core.settings

# Copy startup script
# COPY start.sh /app/start.sh
RUN dos2unix /app/start.sh && chmod +x /app/start.sh

# Create directories
RUN mkdir -p /app/media /app/staticfiles

# Expose port
EXPOSE 9002

# Run startup script
CMD ["/app/start.sh"]
