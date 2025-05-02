#!/bin/bash
set -e

# Check if we're running as Celery worker
if [ "$1" = "celery" ]; then
    echo "Starting Celery worker..."
    celery -A app.tasks worker --loglevel=info
    exit 0
fi

if [ "$1" = "beat" ]; then
    echo "Starting Celery beat..."
    celery -A app.tasks beat --loglevel=info
    exit 0
fi

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 0.5
done
echo "Database is ready!"

# Install netcat (used above for waiting for the DB)
apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Create migrations directory if it doesn't exist
mkdir -p app/migrations/versions

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head || (
  echo "Creating initial migrations..."
  alembic revision --autogenerate -m "Initial migration"
  alembic upgrade head
)

# Then run the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload