#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.management import call_command
from django.db import connection


def main():
    print("=" * 50)
    print("Fixing migrations for Render deployment")
    print("=" * 50)

    # Fake the specific problematic migration
    print("Faking migration 0003...")
    call_command('migrate', 'main', '0003_loanapplication_approved_line_and_more', fake=True)

    print("Running remaining migrations...")
    call_command('migrate', 'main')

    print("=" * 50)
    print("Migration fix completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()