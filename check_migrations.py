#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def check_missing_columns():
    with connection.cursor() as cursor:
        # Check main_loan table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='main_loan'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print("Columns in main_loan table:")
        for col in columns:
            print(f"  - {col[0]}")
        
        # Check if amount column exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='main_loan' 
                AND column_name='amount'
            );
        """)
        amount_exists = cursor.fetchone()[0]
        
        if not amount_exists:
            print("\n❌ 'amount' column is MISSING from main_loan table!")
            print("You need to run migrations to add this column.")
        else:
            print("\n✅ 'amount' column exists")

if __name__ == '__main__':
    check_missing_columns()
