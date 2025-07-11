#!/bin/bash

set -e

echo "🚀 Starting Django application..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script directory: $SCRIPT_DIR"

# Change to the Django project directory
cd "$SCRIPT_DIR"
echo "📁 Working directory: $(pwd)"

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found in $(pwd)"
    echo "📋 Contents of current directory:"
    ls -la
    exit 1
fi

echo "✅ Found manage.py in $(pwd)"

# Wait for database
echo "⏳ Waiting for database..."
echo "🔗 Checking database connection to ${PSQL_HOST:-localhost}:${PSQL_PORT:-5432}"
while ! nc -z ${PSQL_HOST:-localhost} ${PSQL_PORT:-5432}; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ Database is ready!"

# Test Django settings
echo "🔧 Testing Django configuration..."
python3 manage.py check --deploy

# Run migrations
echo "📦 Running database migrations..."
python3 manage.py migrate --noinput

# Collect static files
echo "📁 Collecting static files..."
python3 manage.py collectstatic --noinput --clear

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python3 manage.py shell << 'EOF'
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com') 
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Admin123!!')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created successfully!")
else:
    print(f"Superuser '{username}' already exists.")
EOF

# Start server with Gunicorn
echo "🌐 Starting Django server with Gunicorn on 0.0.0.0:8080..."
echo "🔗 Access at: http://localhost:8081"

# Set Gunicorn configuration
WORKERS=${GUNICORN_WORKERS:-4}
TIMEOUT=${GUNICORN_TIMEOUT:-30}
WSGI_MODULE=${DJANGO_WSGI_MODULE:-core.wsgi:application}

exec gunicorn \
    --bind 0.0.0.0:8080 \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    $WSGI_MODULE