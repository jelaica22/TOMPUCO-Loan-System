#!/bin/bash

echo "========================================="
echo "TOMPUCO Loan Management System - Build"
echo "========================================="

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p staticfiles
mkdir -p media

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "========================================="
echo "Build completed successfully!"
echo "========================================="
