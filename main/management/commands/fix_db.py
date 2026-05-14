from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add missing columns to database tables'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('Adding missing columns to database')
        self.stdout.write('=' * 60)
        
        with connection.cursor() as cursor:
            # All missing columns for main_loan table
            loan_columns = [
                'amount decimal(12,2) NULL',
                'approved_line decimal(12,2) NULL',
                'remaining_balance decimal(12,2) NULL',
                'disbursed_date timestamp NULL',
                'status varchar(50) DEFAULT \'pending\'',
            ]
            
            # All missing columns for main_member table
            member_columns = [
                'civil_status varchar(50) NULL',
                'nickname varchar(100) NULL',
                'middle_initial varchar(10) NULL',
                'employment_status varchar(50) NULL',
                'monthly_income decimal(12,2) NULL',
                'employer_name varchar(200) NULL',
                'employer_address text NULL',
                'position varchar(100) NULL',
                'length_of_employment varchar(50) NULL',
            ]
            
            self.stdout.write('\n📦 Adding columns to main_loan table...')
            for col_def in loan_columns:
                col_name = col_def.split()[0]
                sql = f'ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS {col_def};'
                try:
                    cursor.execute(sql)
                    self.stdout.write(f'  ✓ Added {col_name} column')
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write(f'  ✓ {col_name} already exists')
                    else:
                        self.stdout.write(f'  ⚠ {col_name}: {e}')
            
            self.stdout.write('\n📦 Adding columns to main_member table...')
            for col_def in member_columns:
                col_name = col_def.split()[0]
                sql = f'ALTER TABLE main_member ADD COLUMN IF NOT EXISTS {col_def};'
                try:
                    cursor.execute(sql)
                    self.stdout.write(f'  ✓ Added {col_name} column')
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write(f'  ✓ {col_name} already exists')
                    else:
                        self.stdout.write(f'  ⚠ {col_name}: {e}')
            
            # Verify key columns
            self.stdout.write('\n🔍 Verifying critical columns...')
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='main_loan' 
                    AND column_name='amount'
                );
            """)
            if cursor.fetchone()[0]:
                self.stdout.write(self.style.SUCCESS('  ✅ amount column exists in main_loan'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ amount column missing!'))
            
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='main_member' 
                    AND column_name='employment_status'
                );
            """)
            if cursor.fetchone()[0]:
                self.stdout.write(self.style.SUCCESS('  ✅ employment_status column exists in main_member'))
            else:
                self.stdout.write(self.style.ERROR('  ❌ employment_status column missing!'))
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Database fix completed!'))
        self.stdout.write('=' * 60)
