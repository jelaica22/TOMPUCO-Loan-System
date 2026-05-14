#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.db import connection


def add_missing_columns():
    with connection.cursor() as cursor:
        # Check if table exists first
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_name='main_member'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("Table main_member doesn't exist yet, skipping column addition")
            return

        # Add columns using PostgreSQL syntax
        columns = [
            ('civil_status', 'varchar(50) NULL'),
            ('nickname', 'varchar(100) NULL'),
            ('middle_initial', 'varchar(10) NULL')
        ]

        for col_name, col_type in columns:
            try:
                cursor.execute(f"""
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (
                            SELECT 1 
                            FROM information_schema.columns 
                            WHERE table_name='main_member' 
                            AND column_name='{col_name}'
                        ) THEN 
                            ALTER TABLE main_member ADD COLUMN {col_name} {col_type};
                            RAISE NOTICE 'Added {col_name} column';
                        END IF;
                    END $$;
                """)
                print(f"✓ {col_name} column verified/added")
            except Exception as e:
                print(f"Note for {col_name}: {e}")


if __name__ == '__main__':
    print("=" * 50)
    print("Adding missing columns to main_member table")
    print("=" * 50)
    add_missing_columns()
    print("=" * 50)
    print("Done!")