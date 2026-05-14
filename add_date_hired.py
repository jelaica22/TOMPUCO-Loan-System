import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.db import connection

print("Adding date_hired column...")
with connection.cursor() as cursor:
    cursor.execute("ALTER TABLE main_member ADD COLUMN IF NOT EXISTS date_hired date NULL;")
    print("✓ date_hired column added successfully!")

# Verify
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='main_member' 
    AND column_name='date_hired';
""")
if cursor.fetchone():
    print("✅ Verification: date_hired column exists!")
else:
    print("❌ Failed to add date_hired column")
