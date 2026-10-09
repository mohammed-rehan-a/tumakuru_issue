#!/usr/bin/env bash
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput --clear
python3 manage.py migrate --noinput
python3 manage.py loaddata categories_fixture.json || true
