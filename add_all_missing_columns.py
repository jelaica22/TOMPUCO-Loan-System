#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.db import connection

missing_columns = [
    ('main_member', 'previous_employer', 'varchar(200) NULL'),
    ('main_member', 'previous_employer_contact', 'varchar(50) NULL'),
    ('main_member', 'previous_employer_address', 'text NULL'),
    ('main_member', 'previous_position', 'varchar(100) NULL'),
    ('main_member', 'previous_years', 'int NULL'),
    ('main_loanapplication', 'applied_date', 'timestamp NULL'),
    ('main_loanapplication', 'review_notes', 'text NULL'),
]

print("Adding missing columns...")
with connection.cursor() as cursor:
    for table, column, col_type in missing_columns:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {col_type};")
            print(f"  ✓ {table}.{column}")
        except Exception as e:
            print(f"  ⚠ {table}.{column}: {e}")
print("Done!")
