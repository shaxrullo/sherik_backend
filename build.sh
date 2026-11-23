#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python init_admin.py
python init_cities.py
python block_non_id441.py
python manage.py set_webhook
