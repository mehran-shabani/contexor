#!/bin/bash

# Exit on error
set -e

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
  sleep 0.1
done
echo "PostgreSQL started"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if DJANGO_SUPERUSER_PHONE is set
if [ -n "$DJANGO_SUPERUSER_PHONE" ]; then
  echo "Checking for superuser..."
  python manage.py shell -c "
from accounts.models import User
phone = '$DJANGO_SUPERUSER_PHONE'
if not User.objects.filter(phone_number=phone).exists():
    User.objects.create_superuser(phone_number=phone, password='${DJANGO_SUPERUSER_PASSWORD:-admin123}')
    print('Superuser created')
else:
    print('Superuser already exists')
" || true
fi

# Execute CMD
exec "$@"
