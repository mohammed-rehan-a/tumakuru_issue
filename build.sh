#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py loaddata categories_fixture.json

# Auto-create superuser on deployment (because Render Free tier has no shell)
DJANGO_SUPERUSER_PASSWORD=AdminPass123! \
DJANGO_SUPERUSER_USERNAME=admin_render \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
python manage.py createsuperuser --noinput || true
