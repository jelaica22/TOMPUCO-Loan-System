#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def reset_and_migrate():
    print("=" * 60)
    print("COMPLETE DATABASE RESET AND MIGRATION")
    print("=" * 60)
    
    with connection.cursor() as cursor:
        # Drop all tables and start fresh
        print("\n📦 Dropping all tables...")
        cursor.execute("""
            DO main DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END main;
        """)
        print("  ✓ All tables dropped")
        
        # Delete migration records
        print("\n📦 Clearing migration history...")
        call_command('migrate', '--fake', 'zero', verbosity=0)
        print("  ✓ Migration history cleared")
    
    # Create fresh migrations
    print("\n📦 Creating fresh migrations...")
    call_command('makemigrations', 'main', verbosity=1)
    call_command('makemigrations', 'staff', verbosity=1)
    call_command('makemigrations', 'cashier', verbosity=1)
    call_command('makemigrations', 'committee', verbosity=1)
    call_command('makemigrations', 'manager', verbosity=1)
    call_command('makemigrations', 'admin_panel', verbosity=1)
    call_command('makemigrations', 'reports', verbosity=1)
    
    # Apply migrations
    print("\n📦 Applying migrations...")
    call_command('migrate', verbosity=1)
    
    print("\n" + "=" * 60)
    print("✅ DATABASE RESET AND MIGRATION COMPLETED!")
    print("=" * 60)

if __name__ == '__main__':
    reset_and_migrate()
