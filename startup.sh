#!/bin/bash

echo "🚀 Starting application..."

# Run migrations on startup
echo "🔄 Running migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser if needed..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@tompuco.com', 'admin123')
    print('✅ Superuser created!')
else:
    print('✅ Superuser already exists')
"

# Start the application
echo "🌟 Starting Daphne server..."
daphne -b 0.0.0.0 -p $PORT tompuco.asgi:application