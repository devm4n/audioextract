#!/usr/bin/env bash
set -e

uv run manage.py migrate --noinput
uv run manage.py collectstatic --noinput

uv run manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = '$DJANGO_SUPERUSER_EMAIL' or 'admin@example.com'
password = '$DJANGO_SUPERUSER_PASSWORD' or 'admin'
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(username='admin', email=email, password=password)
    print('Superuser created')
else:
    print('Superuser already exists')
"

exec "$@"
