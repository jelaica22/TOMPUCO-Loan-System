#!/bin/bash

echo "========================================="
echo "TOMPUCO Loan Management System - Build"
echo "========================================="

# Exit on error
set -e

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating directories..."
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist (skip if no database)
echo "Checking for superuser..."
python manage.py shell <<EOF
import os
import sys
from django.contrib.auth import get_user_model
User = get_user_model()
try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@tompuco.com', 'admin123')
        print('✓ Superuser created successfully')
    else:
        print('✓ Superuser already exists')
except Exception as e:
    print(f"Note: Could not create superuser: {e}")
    print("This is normal if database isn't ready yet.")
EOF

echo "========================================="
echo "Build completed successfully!"
echo "========================================="