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

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migration fix
echo "Running migration fixes..."
python fix_migrations.py

# Run any remaining migrations
echo "Running remaining migrations..."
python manage.py migrate --noinput

echo "========================================="
echo "Build completed successfully!"
echo "========================================="