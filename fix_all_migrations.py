#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def fix_all_migrations():
    print("=" * 60)
    print("Fixing all migrations for all apps")
    print("=" * 60)
    
    apps = ['main', 'staff', 'cashier', 'committee', 'manager', 'admin_panel', 'reports']
    
    for app in apps:
        print(f"\n📦 Processing {app}...")
        try:
            call_command('makemigrations', app, verbosity=0)
            print(f"  ✓ Migrations created for {app}")
        except Exception as e:
            print(f"  Note for {app}: {e}")
    
    print("\n" + "=" * 60)
    print("Applying all migrations...")
    print("=" * 60)
    
    call_command('migrate', verbosity=1)
    
    print("\n" + "=" * 60)
    print("Migration fix completed!")
    print("=" * 60)

if __name__ == '__main__':
    fix_all_migrations()
