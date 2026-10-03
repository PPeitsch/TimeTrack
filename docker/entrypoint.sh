#!/bin/sh
# Prepares the database and then runs the container command (gunicorn).
set -e

# Without SECRET_KEY, generate one once in the data volume; the app reads it
# through SECRET_KEY_FILE, also from `docker compose exec web flask ...`.
if [ -z "$SECRET_KEY" ] && [ -n "$SECRET_KEY_FILE" ] && [ ! -s "$SECRET_KEY_FILE" ]; then
    python -c 'import secrets; print(secrets.token_hex(32))' > "$SECRET_KEY_FILE"
    chmod 600 "$SECRET_KEY_FILE"
fi

# The database container may still be starting: retry the migrations.
attempt=1
until flask db upgrade; do
    if [ "$attempt" -ge 10 ]; then
        echo "Database not reachable after $attempt attempts." >&2
        exit 1
    fi
    echo "Database not ready, retrying in 3 s ($attempt/10)..."
    attempt=$((attempt + 1))
    sleep 3
done

flask seed defaults

if [ "$SEED_DEMO" = "true" ]; then
    flask seed demo
fi

exec "$@"
