#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting deployment script..."
echo "Environment Verification:"
echo "DB_ENGINE: ${DB_ENGINE:-'Not Set (will default to settings.py)'}"
echo "DB_HOST: ${DB_HOST:-'Not Set'}"
echo "DB_PORT: ${DB_PORT:-'Not Set'}"
echo "DB_NAME: ${DB_NAME:-'Not Set'}"
echo "DB_USER: ${DB_USER:-'Not Set'}"
# Do NOT print DB_PASS

# Detect and print Public IP (Helpful for Whitelisting)
echo "--------------------------------------------------------"
echo "DETECTING PUBLIC IP FOR DATABASE WHITELISTING:"
PUBLIC_IP=$(curl -s --connect-timeout 5 ifconfig.me || echo "Unavailable")
echo "YOUR VPS PUBLIC IP IS: ${PUBLIC_IP}"
echo "Make sure this IP is allowed in Hostinger -> Databases -> Remote MySQL"
echo "--------------------------------------------------------"

# Wait for database to be ready
echo "Checking database connection..."
python manage.py wait_for_db

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Ensure Admin User
echo "Ensuring admin user exists..."
python manage.py ensure_admin

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3