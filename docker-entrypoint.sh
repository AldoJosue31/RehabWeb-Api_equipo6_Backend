#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time

host = os.getenv('MYSQL_HOST', 'db')
port = int(os.getenv('MYSQL_PORT', '3306'))

for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f'MySQL available at {host}:{port}')
            break
    except OSError:
        if attempt == 59:
            raise
        print(f'Waiting for MySQL at {host}:{port}...')
        time.sleep(2)
PY

python manage.py migrate
exec "$@"
