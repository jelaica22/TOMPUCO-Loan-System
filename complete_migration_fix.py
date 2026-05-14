#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

def fix_all():
    print("=" * 60)
    print("COMPLETE DATABASE MIGRATION FIX")
    print("=" * 60)
    
    # List all apps
    apps = ['main', 'staff', 'cashier', 'committee', 'manager', 'admin_panel', 'reports']
    
    print("\n📦 Step 1: Creating migrations for all apps...")
    for app in apps:
        try:
            call_command('makemigrations', app, verbosity=1)
            print(f"  ✓ {app}")
        except Exception as e:
            print(f"  ⚠ {app}: {e}")
    
    print("\n📦 Step 2: Applying all migrations...")
    try:
        call_command('migrate', verbosity=1)
        print("  ✓ Migrations applied")
    except Exception as e:
        print(f"  ⚠ Error: {e}")
    
    print("\n📦 Step 3: Adding missing columns directly...")
    with connection.cursor() as cursor:
        # Comprehensive list of all possible columns for main_member
        member_columns = [
            ('civil_status', 'varchar(50) NULL'),
            ('nickname', 'varchar(100) NULL'),
            ('middle_initial', 'varchar(10) NULL'),
            ('employment_status', 'varchar(50) NULL'),
            ('employee_id', 'varchar(100) NULL'),
            ('date_hired', 'date NULL'),
            ('years_with_employer', 'int NULL'),
            ('supervisor_name', 'varchar(200) NULL'),
            ('supervisor_contact', 'varchar(50) NULL'),
            ('monthly_income', 'decimal(12,2) NULL'),
            ('employer_name', 'varchar(200) NULL'),
            ('employer_address', 'text NULL'),
            ('position', 'varchar(100) NULL'),
            ('length_of_employment', 'varchar(50) NULL'),
            ('adjacent_farm', 'text NULL'),
            ('farm_size', 'decimal(12,2) NULL'),
            ('crops_planted', 'text NULL'),
            ('source_of_funds', 'varchar(100) NULL'),
            ('land_area', 'decimal(12,2) NULL'),
            ('land_title', 'varchar(100) NULL'),
            ('business_type', 'varchar(100) NULL'),
            ('business_name', 'varchar(200) NULL'),
            ('business_address', 'text NULL'),
            ('years_in_business', 'int NULL'),
            ('spouse_name', 'varchar(200) NULL'),
            ('spouse_occupation', 'varchar(200) NULL'),
            ('number_of_children', 'int NULL'),
            ('house_ownership', 'varchar(100) NULL'),
            ('monthly_rent', 'decimal(12,2) NULL'),
            ('contact_number', 'varchar(20) NULL'),
            ('alternate_contact', 'varchar(20) NULL'),
            ('emergency_contact', 'varchar(20) NULL'),
            ('emergency_contact_name', 'varchar(200) NULL'),
        ]
        
        # Comprehensive list for main_loan table
        loan_columns = [
            ('member_id', 'int NULL'),
            ('borrower_id', 'int NULL'),
            ('amount', 'decimal(12,2) NULL'),
            ('approved_line', 'decimal(12,2) NULL'),
            ('remaining_balance', 'decimal(12,2) NULL'),
            ('disbursed_date', 'timestamp NULL'),
            ('status', "varchar(50) DEFAULT 'pending'"),
            ('application_date', 'timestamp NULL'),
            ('approval_date', 'timestamp NULL'),
            ('rejection_reason', 'text NULL'),
            ('notes', 'text NULL'),
            ('interest_rate', 'decimal(5,2) NULL'),
            ('term_months', 'int NULL'),
            ('monthly_payment', 'decimal(12,2) NULL'),
            ('total_payment', 'decimal(12,2) NULL'),
            ('paid_amount', 'decimal(12,2) NULL'),
            ('last_payment_date', 'timestamp NULL'),
            ('next_payment_date', 'timestamp NULL'),
            ('loan_number', 'varchar(50) NULL'),
        ]
        
        # Add columns to main_loan
        print("\n  Adding columns to main_loan...")
        for col_name, col_type in loan_columns:
            try:
                cursor.execute(f"ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                print(f"    ✓ {col_name}")
            except Exception as e:
                if 'already exists' in str(e):
                    print(f"    ✓ {col_name} (exists)")
                else:
                    print(f"    ⚠ {col_name}: {str(e)[:50]}")
        
        # Add columns to main_member
        print("\n  Adding columns to main_member...")
        for col_name, col_type in member_columns:
            try:
                cursor.execute(f"ALTER TABLE main_member ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                print(f"    ✓ {col_name}")
            except Exception as e:
                if 'already exists' in str(e):
                    print(f"    ✓ {col_name} (exists)")
                else:
                    print(f"    ⚠ {col_name}: {str(e)[:50]}")
        
        # Add columns to main_loanapplication
        loanapp_columns = [
            ('amount', 'decimal(12,2) NULL'),
            ('approved_amount', 'decimal(12,2) NULL'),
            ('status', "varchar(50) DEFAULT 'pending'"),
            ('application_date', 'timestamp NULL'),
            ('review_date', 'timestamp NULL'),
            ('approval_date', 'timestamp NULL'),
        ]
        
        print("\n  Adding columns to main_loanapplication...")
        for col_name, col_type in loanapp_columns:
            try:
                cursor.execute(f"ALTER TABLE main_loanapplication ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                print(f"    ✓ {col_name}")
            except Exception as e:
                if 'already exists' in str(e):
                    print(f"    ✓ {col_name} (exists)")
                else:
                    print(f"    ⚠ {col_name}: {str(e)[:50]}")
        
        # Add columns to main_paymentschedule
        paymentschedule_columns = [
            ('updated_at', 'timestamp NULL'),
            ('created_at', 'timestamp NULL'),
            ('paid_date', 'timestamp NULL'),
            ('due_date', 'date NULL'),
            ('amount_due', 'decimal(12,2) NULL'),
            ('amount_paid', 'decimal(12,2) NULL'),
            ('status', "varchar(50) DEFAULT 'pending'"),
        ]
        
        print("\n  Adding columns to main_paymentschedule...")
        for col_name, col_type in paymentschedule_columns:
            try:
                cursor.execute(f"ALTER TABLE main_paymentschedule ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                print(f"    ✓ {col_name}")
            except Exception as e:
                if 'already exists' in str(e):
                    print(f"    ✓ {col_name} (exists)")
                else:
                    print(f"    ⚠ {col_name}: {str(e)[:50]}")
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE DATABASE FIX COMPLETED!")
    print("=" * 60)

if __name__ == '__main__':
    fix_all()
