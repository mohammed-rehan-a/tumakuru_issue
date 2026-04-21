#!/bin/bash
# ============================================================
# Tumakuru Civic Portal — Quick Setup Script
# ============================================================

set -e

echo ""
echo "============================================================"
echo "  TUMAKURU CITY CORPORATION — CIVIC ISSUE PORTAL"
echo "  Setup Script"
echo "============================================================"
echo ""

# Check Python
python3 --version || { echo "Python3 not found!"; exit 1; }

echo "[1/6] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[2/6] Installing dependencies..."
pip install -r requirements.txt

echo "[3/6] Running database migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations reports
python manage.py migrate

echo "[4/6] Loading issue categories..."
python manage.py loaddata categories_fixture.json

echo "[5/6] Collecting static files..."
python manage.py collectstatic --noinput

echo "[6/6] Creating superuser..."
echo ""
echo "Please create an admin account:"
python manage.py createsuperuser

echo ""
echo "============================================================"
echo "  SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "  Start the server with:"
echo "    source venv/bin/activate"
echo "    python manage.py runserver"
echo ""
echo "  Then visit:"
echo "    http://127.0.0.1:8000/        — Main Portal"
echo "    http://127.0.0.1:8000/admin/  — Admin Panel"
echo ""
echo "============================================================"
