from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Add missing columns to database tables'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write('Adding missing columns to database')
        self.stdout.write('=' * 60)
        
        with connection.cursor() as cursor:
            sql_commands = [
                'ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS amount decimal(12,2) NULL;',
                'ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS approved_line decimal(12,2) NULL;',
                'ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS remaining_balance decimal(12,2) NULL;',
                'ALTER TABLE main_loan ADD COLUMN IF NOT EXISTS disbursed_date timestamp NULL;',
                'ALTER TABLE main_member ADD COLUMN IF NOT EXISTS civil_status varchar(50) NULL;',
                'ALTER TABLE main_member ADD COLUMN IF NOT EXISTS nickname varchar(100) NULL;',
                'ALTER TABLE main_member ADD COLUMN IF NOT EXISTS middle_initial varchar(10) NULL;',
            ]
            
            for sql in sql_commands:
                try:
                    cursor.execute(sql)
                    self.stdout.write(f'✓ Executed: {sql[:60]}...')
                except Exception as e:
                    if 'already exists' in str(e):
                        self.stdout.write('✓ Column already exists')
                    else:
                        self.stdout.write(f'⚠ Note: {e}')
            
            # Verify
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
                self.stdout.write(self.style.SUCCESS('\n✅ SUCCESS: amount column exists!'))
            else:
                self.stdout.write(self.style.ERROR('\n❌ FAILED: amount column still missing!'))
        
        self.stdout.write('=' * 60)
        self.stdout.write('Database fix completed!')
        self.stdout.write('=' * 60)
