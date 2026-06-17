#!/bin/sh
set -e

mkdir -p /app/data/avatars
chown -R app:app /app/data

exec su -s /bin/sh app -c "$*"
