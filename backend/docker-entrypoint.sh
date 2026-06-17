#!/bin/sh
set -e

mkdir -p /app/data/avatars
chown -R app:app /app/data

exec su app -s /bin/sh -c 'cd /app && PYTHONPATH=/app alembic upgrade head && exec env PYTHONPATH=/app uvicorn app.main:app --host 0.0.0.0 --port 8000'
