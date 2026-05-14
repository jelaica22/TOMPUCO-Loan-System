#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.db import connection

def add_missing_columns():
    with connection.cursor() as cursor:
        # Add civil_status column
        try:
            cursor.execute("ALTER TABLE main_member ADD COLUMN civil_status varchar(50) NULL;")
            print("✓ Added civil_status column")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ civil_status column already exists")
            else:
                print(f"Note: {e}")
        
        # Add nickname column
        try:
            cursor.execute("ALTER TABLE main_member ADD COLUMN nickname varchar(100) NULL;")
            print("✓ Added nickname column")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ nickname column already exists")
            else:
                print(f"Note: {e}")
        
        # Add middle_initial column
        try:
            cursor.execute("ALTER TABLE main_member ADD COLUMN middle_initial varchar(10) NULL;")
            print("✓ Added middle_initial column")
        except Exception as e:
            if "already exists" in str(e):
                print("✓ middle_initial column already exists")
            else:
                print(f"Note: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("Adding missing columns to main_member table")
    print("=" * 50)
    add_missing_columns()
    print("=" * 50)
    print("Done!")
