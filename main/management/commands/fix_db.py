from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add all missing columns to database tables'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('Adding ALL missing columns to database')
        self.stdout.write('=' * 60)
        
        with connection.cursor() as cursor:
            # ALL possible columns for main_member table
            member_columns = [
                'civil_status varchar(50) NULL',
                'nickname varchar(100) NULL',
                'middle_initial varchar(10) NULL',
                'employment_status varchar(50) NULL',
                'employee_id varchar(100) NULL',
                'monthly_income decimal(12,2) NULL',
                'employer_name varchar(200) NULL',
                'employer_address text NULL',
                'position varchar(100) NULL',
                'length_of_employment varchar(50) NULL',
                'adjacent_farm text NULL',
                'farm_size decimal(12,2) NULL',
                'crops_planted text NULL',
                'source_of_funds varchar(100) NULL',
                'land_area decimal(12,2) NULL',
                'land_title varchar(100) NULL',
                'business_type varchar(100) NULL',
                'business_name varchar(200) NULL',
                'business_address text NULL',
                'years_in_business int NULL',
                'spouse_name varchar(200) NULL',
                'spouse_occupation varchar(200) NULL',
                'number_of_children int NULL',
                'house_ownership varchar(100) NULL',
                'monthly_rent decimal(12,2) NULL',
            ]
            
            # ALL possible columns for main_loan table
            loan_columns = [
                'amount decimal(12,2) NULL',
                'approved_line decimal(12,2) NULL',
                'remaining_balance decimal(12,2) NULL',
                'disbursed_date timestamp NULL',
                'status varchar(50) DEFAULT \'pending\'',
                'application_date timestamp NULL',
                'approval_date timestamp NULL',
                'rejection_reason text NULL',
                'notes text NULL',
            ]
            
            self.stdout.write('\n📦 Adding columns to main_loan table...')
            for col_def in loan_columns:
                col_name = col_def.split()[0]
                sql = f'ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS {col_def};'
                try:
                    cursor.execute(sql)
                    self.stdout.write(f'  ✓ {col_name}')
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write(f'  ✓ {col_name} (exists)')
                    else:
                        self.stdout.write(f'  ⚠ {col_name}: {str(e)[:50]}')
            
            self.stdout.write('\n📦 Adding columns to main_member table...')
            for col_def in member_columns:
                col_name = col_def.split()[0]
                sql = f'ALTER TABLE main_member ADD COLUMN IF NOT EXISTS {col_def};'
                try:
                    cursor.execute(sql)
                    self.stdout.write(f'  ✓ {col_name}')
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write(f'  ✓ {col_name} (exists)')
                    else:
                        self.stdout.write(f'  ⚠ {col_name}: {str(e)[:50]}')
            
            # Verify critical columns
            self.stdout.write('\n🔍 Verifying critical columns...')
            
            critical_columns = ['amount', 'employment_status', 'employee_id']
            for col_name in critical_columns:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name='main_member' 
                        AND column_name='{col_name}'
                    );
                """)
                if cursor.fetchone()[0]:
                    self.stdout.write(self.style.SUCCESS(f'  ✅ {col_name} exists in main_member'))
                else:
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT 1 
                            FROM information_schema.columns 
                            WHERE table_name='main_loan' 
                            AND column_name='{col_name}'
                        );
                    """)
                    if cursor.fetchone()[0]:
                        self.stdout.write(self.style.SUCCESS(f'  ✅ {col_name} exists in main_loan'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  ❌ {col_name} still missing!'))
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Database fix completed!'))
        self.stdout.write('=' * 60)
