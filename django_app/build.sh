#!/usr/bin/env bash
# Pasos que Render ejecuta cada vez que publica una versión nueva.
set -o errexit   # si un paso falla, se detiene todo

cd "$(dirname "$0")"

pip install -r requirements.txt
python manage.py collectstatic --no-input   # junta el CSS/JS en staticfiles/
python manage.py migrate --no-input         # crea o actualiza las tablas

# Crea la cuenta de administración la primera vez (si definiste las variables
# DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL y DJANGO_SUPERUSER_PASSWORD).
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ]; then
  python manage.py createsuperuser --no-input || echo "La cuenta de administración ya existía."
fi
