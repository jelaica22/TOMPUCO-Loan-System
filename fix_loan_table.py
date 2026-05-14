#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.db import connection

def fix_loan_table():
    with connection.cursor() as cursor:
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
            print("❌ 'amount' column missing, adding it...")
            try:
                cursor.execute("ALTER TABLE main_loan ADD COLUMN amount decimal(12,2) NULL;")
                print("✓ Added amount column to main_loan table")
            except Exception as e:
                print(f"Error adding amount column: {e}")
        else:
            print("✓ amount column already exists")
        
        # Check for other common missing columns
        columns_to_check = [
            ('approved_line', 'decimal(12,2) NULL'),
            ('remaining_balance', 'decimal(12,2) NULL'),
            ('status', "varchar(50) DEFAULT 'pending'"),
            ('disbursed_date', 'timestamp NULL'),
        ]
        
        for col_name, col_type in columns_to_check:
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='main_loan' 
                    AND column_name='{col_name}'
                );
            """)
            if not cursor.fetchone()[0]:
                try:
                    cursor.execute(f"ALTER TABLE main_loan ADD COLUMN {col_name} {col_type};")
                    print(f"✓ Added {col_name} column")
                except Exception as e:
                    print(f"Note for {col_name}: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("Fixing main_loan table columns")
    print("=" * 50)
    fix_loan_table()
    print("=" * 50)
    print("Done!")
