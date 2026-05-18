#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

print("=" * 60)
print("FULL DATABASE RESET AND MIGRATION")
print("=" * 60)

# Drop all tables
print("\n📦 Dropping all tables...")
with connection.cursor() as cursor:
    # Get all table names
    cursor.execute("""
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """)
    tables = cursor.fetchall()
    
    for table in tables:
        try:
            cursor.execute(f'DROP TABLE IF EXISTS "{table[0]}" CASCADE;')
            print(f"  ✓ Dropped {table[0]}")
        except Exception as e:
            print(f"  ⚠ Could not drop {table[0]}: {e}")

print("  ✓ All tables dropped")

# Reset migration history
print("\n📦 Resetting migration history...")
try:
    call_command('migrate', '--fake', 'zero', verbosity=0)
except:
    pass
print("  ✓ Migration history reset")

# Create fresh migrations
print("\n📦 Creating fresh migrations...")
call_command('makemigrations', 'main')
call_command('makemigrations', 'staff')
call_command('makemigrations', 'cashier')
call_command('makemigrations', 'committee')
call_command('makemigrations', 'manager')
call_command('makemigrations', 'admin_panel')
call_command('makemigrations', 'reports')
print("  ✓ Migrations created")

# Apply migrations
print("\n📦 Applying migrations...")
call_command('migrate', verbosity=1)

print("\n" + "=" * 60)
print("✅ DATABASE RESET COMPLETED!")
print("=" * 60)
