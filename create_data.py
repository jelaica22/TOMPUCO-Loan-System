import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import LoanProduct, Member, LoanApplication, Loan
from datetime import date, timedelta

print("Creating data...")

# Create product
product, created = LoanProduct.objects.get_or_create(
    name='APCP',
    defaults={
        'display_name': 'APCP - Agricultural Loan',
        'loan_type': 'APCP',
        'interest_rate': 15.00,
        'term_months': 12,
        'term_days': 360,
        'min_amount': 10000,
        'max_amount': 500000,
        'requires_comaker': False,
        'is_active': True,
    }
)
print(f"Product: {product.name}")

# Create staff
staff_user, created = User.objects.get_or_create(
    username='staff_user',
    defaults={
        'email': 'staff@test.com',
        'first_name': 'Maria',
        'last_name': 'Santos',
        'is_staff': True
    }
)
staff_user.set_password('staff123')
staff_user.save()
print(f"Staff: {staff_user.username}")

# Create member
member_user, created = User.objects.get_or_create(
    username='member_juan',
    defaults={
        'email': 'juan@test.com',
        'first_name': 'Juan',
        'last_name': 'Dela Cruz'
    }
)
member_user.set_password('member123')
member_user.save()

member, created = Member.objects.get_or_create(
    membership_number='M-10001',
    defaults={
        'user': member_user,
        'first_name': 'Juan',
        'last_name': 'Dela Cruz',
        'contact_number': '09123456789',
        'residence_address': '123 Test St.',
        'monthly_income': 30000,
        'is_active': True,
        'kyc_completed': True
    }
)
print(f"Member: {member.first_name} {member.last_name}")

# Create application
application = LoanApplication.objects.create(
    application_id='APCP-2026-0001',
    member=member,
    applicant_user=staff_user,
    loan_product=product,
    requested_amount=50000,
    approved_line=45000,
    purpose='Rice farming',
    collateral_offered='Farm land',
    mode_of_payment='monthly',
    status='manager_approved',
    date_applied=date.today(),
    loan_term=12
)
print(f"Application: {application.application_id} - {application.status}")

# Create loan
loan = Loan.objects.create(
    loan_number='LN-2026-0001',
    application=application,
    borrower=member,
    loan_product=product,
    principal_amount=45000,
    interest_rate=15.00,
    term_months=12,
    term_days=360,
    disbursement_date=date.today(),
    due_date=date.today().replace(year=date.today().year + 1),
    next_due_date=date.today() + timedelta(days=30),
    remaining_balance=45000,
    monthly_payment=4050,
    total_interest=3600,
    total_payable_amount=48600,
    status='active',
    created_by=staff_user
)
print(f"Loan: {loan.loan_number} - {loan.status}")

print("\n" + "="*50)
print("SUMMARY:")
print(f"Products: {LoanProduct.objects.count()}")
print(f"Members: {Member.objects.count()}")
print(f"Applications: {LoanApplication.objects.count()}")
print(f"Loans: {Loan.objects.count()}")
print("="*50)
print("Login: staff_user / staff123")
print("="*50)