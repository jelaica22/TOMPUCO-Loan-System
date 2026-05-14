#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command

print("=" * 50)
print("Running migrations...")
print("=" * 50)

try:
    # Make migrations first
    call_command('makemigrations')
    print("✓ Migrations created")
except Exception as e:
    print(f"Note: {e}")

# Apply migrations
call_command('migrate', '--noinput')
print("✓ Migrations applied")

print("=" * 50)
print("Migration fix completed!")
print("=" * 50)