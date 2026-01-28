#!/usr/bin/env bash
set -e

echo "Checking database state..."

psql "$DATABASE_URL" -Atc \
"SELECT 1 FROM information_schema.tables WHERE table_name='django_migrations';" \
| grep -q 1 \
|| (
  echo "Database is empty. Importing dump.sql..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 < dump.sql
)

echo "Applying migrations..."
python manage.py migrate --fake-initial

echo "Starting server..."
exec gunicorn config.asgi:application \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT}
