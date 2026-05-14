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
    cursor.execute("""
        DO UTF8 DECLARE
            r RECORD;
        BEGIN
            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
            END LOOP;
        END UTF8;
    """)
    print("  ✓ All tables dropped")

# Reset migration history
print("\n📦 Resetting migration history...")
call_command('migrate', '--fake', 'zero', verbosity=0)
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
