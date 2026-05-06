#!/bin/sh
set -e

echo "==> Starting Ecoride Assembly"
echo "==> PORT: ${PORT}"
echo "==> DATABASE_URL set: $([ -n "$DATABASE_URL" ] && echo YES || echo NO)"

echo "==> Running collectstatic..."
python manage.py collectstatic --noinput

echo "==> Running migrate..."
python manage.py migrate

echo "==> Starting gunicorn on port ${PORT:-8000}..."
exec gunicorn core.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 120
