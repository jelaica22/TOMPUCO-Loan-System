#!/usr/bin/env python
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.db import connection

def apply_fix():
    db_engine = settings.DATABASES['default']['ENGINE']
    
    if 'sqlite' in db_engine:
        print("Running on SQLite - skipping direct fix (use migrations)")
        return
    
    print("Running on PostgreSQL - applying direct column fixes...")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Read and execute SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'direct_fix.sql')
        
        if os.path.exists(sql_file):
            with open(sql_file, 'r') as f:
                sql_commands = f.read()
                
            # Split and execute each command
            for command in sql_commands.split(';'):
                if command.strip():
                    try:
                        cursor.execute(command)
                        print(f"✓ Executed: {command[:50]}...")
                    except Exception as e:
                        if "already exists" in str(e) or "duplicate" in str(e):
                            print(f"Note: Column already exists")
                        else:
                            print(f"Error: {e}")
        
        # Verify amount column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='main_loan' 
                AND column_name='amount'
            );
        """)
        exists = cursor.fetchone()[0]
        
        if exists:
            print("\n✅ 'amount' column successfully added to main_loan table")
        else:
            print("\n❌ 'amount' column still missing!")
    
    print("=" * 50)
    print("Direct fix completed!")

if __name__ == '__main__':
    apply_fix()
