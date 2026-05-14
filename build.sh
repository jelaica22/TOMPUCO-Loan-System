#!/bin/bash

echo "========================================="
echo "TOMPUCO Loan Management System - Build"
echo "========================================="

pip install --upgrade pip
pip install -r requirements.txt
mkdir -p staticfiles media

# Run comprehensive migration fixes
python fix_all_migrations.py
python fix_loan_table.py
python add_columns.py

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

# Create superuser
python create_superuser.py

echo "Build completed!"
