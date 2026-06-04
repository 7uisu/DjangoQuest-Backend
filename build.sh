#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py seed_achievements
python manage.py seed_video_tutorials
python manage.py sync_profile_xp
python manage.py ensure_admin
