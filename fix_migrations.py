#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def main():
    print("=" * 50)
    print("Fixing migrations for Render deployment")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Check if approved_line column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='main_loanapplication' 
                AND column_name='approved_line'
            );
        """)
        column_exists = cursor.fetchone()[0]
        
        if column_exists:
            print("✓ Column 'approved_line' already exists")
            print("✓ Faking migration 0003...")
            call_command('migrate', 'main', '0003_loanapplication_approved_line_and_more', fake=True)
            print("✓ Migration 0003 marked as applied")
        else:
            print("✓ Column doesn't exist, running normal migrations...")
            call_command('migrate', 'main')
    
    print("=" * 50)
    print("Migration fix completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()