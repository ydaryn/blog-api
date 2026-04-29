#!/bin/sh
set -e

echo "Waiting for Redis..."
until redis-cli -h "${BLOG_REDIS_HOST:-redis}" -p "${BLOG_REDIS_PORT:-6379}" ping | grep -q PONG; do
    sleep 1
done
echo "Redis is up."

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py compilemessages || true  

if [ "${BLOG_SEED_DB}" = "true" ]; then
    python manage.py seed
fi

exec "$@"