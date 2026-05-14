#!/bin/bash

echo "========================================="
echo "TOMPUCO Loan Management System - Build"
echo "========================================="

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p staticfiles media

# APPLY DIRECT FIX FIRST (most important)
echo "Applying direct database fixes..."
python apply_direct_fix.py

# Then run migrations
python manage.py makemigrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python create_superuser.py

echo "========================================="
echo "Build completed!"
echo "========================================="
