import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import Member, LoanProduct, LoanApplication, Notification

def create_ready_loan():
    print("=" * 70)
    print("CREATING SAMPLE LOAN APPLICATION")
    print("=" * 70)
    
    # Create Staff
    staff, _ = User.objects.get_or_create(username='staff_maria', defaults={'first_name':'Maria','last_name':'Santos','email':'maria@tompuco.com','is_staff':True})
    if _:
        staff.set_password('staff123')
        staff.save()
        print("✓ Staff: staff_maria / staff123")
    
    # Create Member
    member_user, _ = User.objects.get_or_create(username='juan_delacruz', defaults={'first_name':'Juan','last_name':'Dela Cruz','email':'juan@email.com'})
    if _:
        member_user.set_password('member123')
        member_user.save()
        print("✓ Member user created")
    
    # Create Member Profile
    member, _ = Member.objects.get_or_create(user=member_user, defaults={
        'membership_number': f'M-{random.randint(10000,99999)}',
        'first_name': 'Juan', 'last_name': 'Dela Cruz',
        'contact_number': '09123456789',
        'residence_address': '123 Makati City',
        'monthly_income': Decimal('35000'),
        'is_active': True
    })
    print(f"✓ Member: {member.membership_number}")
    
    # Create Loan Product
    product, _ = LoanProduct.objects.get_or_create(name='APCP', defaults={
        'display_name': 'Agricultural Credit Program',
        'interest_rate': Decimal('20'), 'term_months': 12,
        'min_amount': Decimal('10000'), 'max_amount': Decimal('500000'),
        'is_active': True
    })
    print("✓ Loan product created")
    
    # Create Application
    approved = Decimal('80000')
    charges = approved * Decimal('0.03') + approved * Decimal('0.02') + approved * Decimal('0.0132') + Decimal('35') + Decimal('200')
    net = approved - charges
    
    app, _ = LoanApplication.objects.get_or_create(application_id='APCP-2026-READY-001', defaults={
        'member': member, 'applicant_user': member_user, 'loan_product': product,
        'requested_amount': Decimal('100000'), 'approved_line': approved,
        'service_charge': approved * Decimal('0.03'), 'cbu_retention': approved * Decimal('0.02'),
        'insurance_charge': approved * Decimal('0.0132'), 'service_fee': Decimal('35'),
        'notarial_fee': Decimal('200'), 'total_deductions': charges, 'net_proceeds': net,
        'interest_rate': Decimal('20'), 'loan_term': 12, 'status': 'manager_approved',
        'valid_id_verified': True, 'collateral_verified': True
    })
    print(f"✓ Application: {app.application_id}")
    print(f"✓ Status: manager_approved")
    print(f"✓ Net Proceeds: ₱{net:,.2f}")
    print("\n✅ Login: staff_maria / staff123")

if __name__ == '__main__':
    create_ready_loan()
