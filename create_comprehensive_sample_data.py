# create_comprehensive_sample_data.py
import os
import django
from datetime import datetime, timedelta, date
import random
from decimal import Decimal
from decimal import Decimal
from main.models import LoanApplication, Loan, Member, LoanProduct, Payment

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from main.models import Member, Loan, LoanApplication
from staff.models import StaffProfile
from payments.models import Payment

# ==================== CONFIGURATION ====================
NUM_MEMBERS = 50
NUM_APPLICATIONS_PER_MEMBER = (1, 3)  # min, max
NUM_LOANS_PER_MEMBER = (1, 2)  # min, max

# Loan types with their properties
LOAN_TYPES = {
    'APCP': {'name': 'Agricultural Production Credit Program', 'interest': 15, 'min': 10000, 'max': 1000000},
    'NCL': {'name': 'National Commodity Loan', 'interest': 20, 'min': 5000, 'max': 500000},
    'SALARY': {'name': 'Salary Loan', 'interest': 8, 'min': 5000, 'max': 500000},
    'COLLATERAL': {'name': 'Collateral Loan', 'interest': 20, 'min': 20000, 'max': 2000000},
    'B2B': {'name': 'Back-to-Back Loan', 'interest': 20, 'min': 50000, 'max': 5000000},
    'PROVIDENTIAL': {'name': 'Providential Loan', 'interest': 16, 'min': 10000, 'max': 1000000},
    'TRADE': {'name': 'Trade Loan', 'interest': 18, 'min': 10000, 'max': 500000},
}

# Status flow for applications
APPLICATION_STATUSES = [
    'pending_staff_review',
    'with_committee',
    'line_approved',
    'pending_manager_approval',
    'manager_approved',
    'rejected',
    'needs_revision'
]

# Loan statuses
LOAN_STATUSES = ['active', 'active', 'active', 'overdue', 'paid', 'restructured']

# Filipino names for realistic data
FIRST_NAMES = [
    'Juan', 'Maria', 'Jose', 'Ana', 'Pedro', 'Rosa', 'Antonio', 'Elena', 'Ricardo', 'Carmen',
    'Manuel', 'Teresa', 'Francisco', 'Luz', 'Ramon', 'Corazon', 'Gregorio', 'Julieta', 'Vicente', 'Nelia',
    'Ernesto', 'Mila', 'Rogelio', 'Pilar', 'Rolando', 'Letty', 'Danilo', 'Nora', 'Felipe', 'Aida',
    'Jesus', 'Lorna', 'Efren', 'Marlyn', 'Reynaldo', 'Beth', 'Crisanto', 'Fe', 'Edgardo', 'Grace',
    'Noel', 'Luzviminda', 'Arturo', 'Rowena', 'Emmanuel', 'Cecilia', 'Romeo', 'Lerma', 'Fernando', 'Marilou'
]

LAST_NAMES = [
    'Dela Cruz', 'Santos', 'Reyes', 'Garcia', 'Fernandez', 'Mendoza', 'Villanueva', 'Torres', 'Ramirez', 'Flores',
    'Gonzales', 'Rivera', 'Castillo', 'Cruz', 'Aquino', 'Marcos', 'Macapagal', 'Arroyo', 'Estrada', 'Roxas',
    'Aguilar', 'Bautista', 'Castro', 'Domingo', 'Escobar', 'Guzman', 'Hernandez', 'Ibarra', 'Jimenez', 'Lopez',
    'Magsaysay', 'Navarro', 'Ocampo', 'Pascual', 'Quinto', 'Ramos', 'Serrano', 'Tolentino', 'Uy', 'Valdez',
    'Ybanez', 'Zamora', 'Alcantara', 'Bacalso', 'Cabanes', 'Duran', 'Estrella', 'Fuentes', 'Gatchalian', 'Hizon'
]

# Philippine cities/towns
LOCATIONS = [
    'Brgy. Villareal, Bayawan City', 'Brgy. Kalumboyan, Bayawan City', 'Brgy. Nangka, Bayawan City',
    'Brgy. Balabag, Bayawan City', 'Brgy. San Jose, Bayawan City', 'Brgy. Suba, Bayawan City',
    'Brgy. Canlargo, Bayawan City', 'Brgy. Malabugas, Bayawan City', 'Brgy. Tinago, Bayawan City',
    'Brgy. Poblacion, Bayawan City', 'Brgy. Dawis, Bayawan City', 'Brgy. Karahan, Bayawan City',
    'Brgy. Magsaysay, Bayawan City', 'Brgy. Nangka, Bayawan City', 'Brgy. Opao, Bayawan City'
]

# Purpose of loan
PURPOSES = [
    'Farm improvement and crop production',
    'Purchase of farm inputs and fertilizers',
    'Land preparation and cultivation',
    'Harvesting and post-harvest facilities',
    'Livestock raising and poultry production',
    'Business capital for trading',
    'School tuition and educational expenses',
    'Medical emergency and hospitalization',
    'House renovation and improvement',
    'Purchase of farm equipment and machinery',
    'Irrigation system installation',
    'Crop diversification and expansion',
    'Disaster recovery and rehabilitation',
    'Membership share capital increase'
]

# Collateral offered
COLLATERALS = [
    'Farm land with title (TCT No. 12345)',
    'Agricultural machinery and equipment',
    'Rice production area (2.5 hectares)',
    'Sugarcane plantation land',
    'Personal property and improvements',
    'CBU savings and share capital',
    'Vehicle and farm equipment',
    'Agricultural products and harvest',
    'Land title and improvements',
    'Salary deduction authorization'
]

# Farm locations
FARM_LOCATIONS = [
    'Hacienda Dela Cruz, Villareal', 'San Jose Rice Fields', 'Sitio Upper Canlargo',
    'Purok Malipayon, Suba', 'Hacienda Ramirez, Tinago', 'Kalumboyan Agricultural Area',
    'Nangka Valley Farms', 'Malabugas Plantation', 'Canlargo Rice Terraces',
    'Dawis Corn Fields', 'Karahan Vegetable Farms', 'Magsaysay Coconut Plantation'
]


def create_users():
    """Create all system users"""
    print("📝 Creating system users...")

    # Create staff users
    staff_list = [
        ('juan.dela.cruz', 'Juan', 'Dela Cruz', 'staff123'),
        ('maria.santos', 'Maria', 'Santos', 'staff123'),
        ('pedro.reyes', 'Pedro', 'Reyes', 'staff123'),
        ('ana.lim', 'Ana', 'Lim', 'staff123'),
    ]

    for username, first, last, pwd in staff_list:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first,
                'last_name': last,
                'email': f'{username}@tompuco.com',
                'password': make_password(pwd),
                'is_staff': True
            }
        )
        if created:
            print(f"  ✅ Staff: {username} / {pwd}")

        # Create staff profile
        StaffProfile.objects.get_or_create(
            user=user,
            defaults={
                'staff_id': f"STF{random.randint(100, 999)}",
                'position': 'loan_officer',
                'department': 'Loans Department',
                'is_active': True
            }
        )

    # Create committee users
    committee_list = [
        ('antonio.fernandez', 'Antonio', 'Fernandez', 'committee123'),
        ('carmen.garcia', 'Carmen', 'Garcia', 'committee123'),
        ('ricardo.mendoza', 'Ricardo', 'Mendoza', 'committee123'),
    ]

    for username, first, last, pwd in committee_list:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first,
                'last_name': last,
                'email': f'{username}@tompuco.com',
                'password': make_password(pwd),
                'is_staff': True
            }
        )
        if created:
            print(f"  ✅ Committee: {username} / {pwd}")

    # Create manager
    user, created = User.objects.get_or_create(
        username='roberto.villanueva',
        defaults={
            'first_name': 'Roberto',
            'last_name': 'Villanueva',
            'email': 'manager@tompuco.com',
            'password': make_password('manager123'),
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        print(f"  ✅ Manager: roberto.villanueva / manager123")

    # Create cashier users
    cashier_list = [
        ('analiza.reyes', 'Analiza', 'Reyes', 'cashier123'),
        ('jose.martinez', 'Jose', 'Martinez', 'cashier123'),
    ]

    for username, first, last, pwd in cashier_list:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first,
                'last_name': last,
                'email': f'{username}@tompuco.com',
                'password': make_password(pwd),
                'is_staff': True
            }
        )
        if created:
            print(f"  ✅ Cashier: {username} / {pwd}")

    print(f"  ✅ Total users created: {User.objects.count()}")


def create_members():
    """Create 50 members with realistic data"""
    print(f"\n👥 Creating {NUM_MEMBERS} members...")

    members = []
    for i in range(NUM_MEMBERS):
        first_name = FIRST_NAMES[i % len(FIRST_NAMES)]
        last_name = LAST_NAMES[i % len(LAST_NAMES)]
        membership_number = f"M-2025-{1000 + i:04d}"
        contact = f"09{random.randint(100000000, 999999999)}"

        # Determine if employee or farmer
        is_employee = random.choice([True, False, False, False])  # 25% employees
        employer_name = ''
        if is_employee:
            employers = ['DepEd Bayawan', 'City Hall Bayawan', 'LGU Bayawan', 'Eastern Savings Bank',
                         'Rural Bank of Bayawan']
            employer_name = random.choice(employers)

        # Create user account for member
        username = f"{first_name.lower()}.{last_name.lower()}".replace(' ', '')
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{username}@example.com",
                'password': make_password('member123')
            }
        )

        if created:
            # Create member profile
            member = Member.objects.create(
                user=user,
                membership_number=membership_number,
                first_name=first_name,
                last_name=last_name,
                contact_number=contact,
                residence_address=random.choice(LOCATIONS),
                birthdate=date(random.randint(1960, 1995), random.randint(1, 12), random.randint(1, 28)),
                gender=random.choice(['Male', 'Female']),
                is_employee=is_employee,
                employer_name=employer_name,
                farm_location=random.choice(FARM_LOCATIONS) if not is_employee else '',
                is_active=True
            )
            members.append(member)
            print(f"  ✅ Member {i + 1}: {first_name} {last_name} ({membership_number})")

    print(f"  ✅ Total members created: {len(members)}")
    return members


def create_loan_applications(members):
    """Create loan applications for members"""
    print(f"\n📋 Creating loan applications...")

    applications = []
    total_apps = 0

    for member in members:
        num_apps = random.randint(*NUM_APPLICATIONS_PER_MEMBER)

        for j in range(num_apps):
            loan_type = random.choice(list(LOAN_TYPES.keys()))
            loan_info = LOAN_TYPES[loan_type]
            requested_amount = random.randint(loan_info['min'], min(loan_info['max'], 200000))

            # Random date within last 6 months
            days_ago = random.randint(1, 180)
            date_applied = date.today() - timedelta(days=days_ago)

            # Determine status based on date
            if days_ago < 30:
                status = random.choice(['pending_staff_review', 'with_committee', 'line_approved'])
            elif days_ago < 90:
                status = random.choice(['line_approved', 'pending_manager_approval', 'manager_approved'])
            else:
                status = random.choice(['manager_approved', 'rejected', 'needs_revision'])

            application_id = f"APCP-2026-{3000 + total_apps:04d}"

            app = LoanApplication.objects.create(
                application_id=application_id,
                member=member,
                loan_type=loan_type,
                requested_amount=requested_amount,
                purpose=random.choice(PURPOSES),
                collateral=random.choice(COLLATERALS),
                status=status,
                date_applied=date_applied
            )
            applications.append(app)
            total_apps += 1

            if total_apps % 10 == 0:
                print(f"  📋 Created {total_apps} applications...")

    print(f"  ✅ Total applications created: {len(applications)}")
    return applications


def create_loans(members):
    """Create loan records for members"""
    print(f"\n💰 Creating loan records...")

    loans = []
    total_loans = 0

    for member in members:
        num_loans = random.randint(*NUM_LOANS_PER_MEMBER)

        for j in range(num_loans):
            loan_type = random.choice(list(LOAN_TYPES.keys()))
            loan_info = LOAN_TYPES[loan_type]
            principal = random.randint(loan_info['min'], min(loan_info['max'], 150000))
            interest_rate = loan_info['interest']

            # Calculate monthly payment using diminishing method
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** 12) / ((1 + monthly_rate) ** 12 - 1)
            total_interest = (monthly_payment * 12) - principal
            total_payable = principal + total_interest

            # Random disbursement date within last 2 years
            days_ago = random.randint(0, 730)
            disbursement_date = date.today() - timedelta(days=days_ago)
            due_date = disbursement_date + timedelta(days=360)

            # Determine loan status
            if days_ago < 30:
                status = 'active'
                remaining_balance = principal
            elif days_ago < 180:
                status = random.choice(['active', 'active', 'overdue'])
                months_paid = random.randint(1, 5)
                remaining_balance = principal - (monthly_payment * months_paid)
            elif days_ago < 365:
                status = random.choice(['active', 'overdue', 'overdue'])
                months_paid = random.randint(5, 10)
                remaining_balance = principal - (monthly_payment * months_paid)
            else:
                status = random.choice(['paid', 'paid', 'overdue', 'restructured'])
                remaining_balance = principal * random.uniform(0, 0.3)

            loan_number = f"LN-2025-{5000 + total_loans:04d}"

            loan = Loan.objects.create(
                loan_number=loan_number,
                borrower=member,
                loan_type=loan_type,
                principal_amount=principal,
                interest_rate=interest_rate,
                monthly_payment=monthly_payment,
                total_interest=total_interest,
                total_payable=total_payable,
                remaining_balance=remaining_balance,
                disbursement_date=disbursement_date,
                due_date=due_date,
                next_due_date=disbursement_date + timedelta(days=30 * (random.randint(1, 11))),
                status=status,
                paid_amount=principal - remaining_balance if status != 'paid' else principal,
                last_payment_date=disbursement_date + timedelta(
                    days=30 * random.randint(1, 10)) if status != 'paid' else due_date
            )
            loans.append(loan)
            total_loans += 1

            if total_loans % 10 == 0:
                print(f"  💰 Created {total_loans} loans...")

    print(f"  ✅ Total loans created: {len(loans)}")
    return loans


@login_required
@user_passes_test(is_staff)
def create_loan(request, pk):
    """Create loan from approved application (after charges added)"""
    staff_profile = request.user.staff_profile
    from datetime import date, timedelta

    application = get_object_or_404(LoanApplication, pk=pk)

    if application.status != 'ready_for_disbursement':
        messages.error(request, 'Application must have charges added before creating loan.')
        return redirect('staff:staff_applications')

    if request.method == 'POST':
        loan_count = Loan.objects.count() + 1
        loan_number = f"LN-{date.today().year}-{loan_count:04d}"

        principal = float(application.approved_line)
        interest_rate = float(application.loan_product.interest_rate)

        # Get term_months from POST data or use default
        term_months = request.POST.get('term_months')

        # Validate term_months
        if not term_months:
            messages.error(request, 'Please select a loan term.')
            return redirect('staff:create_loan', pk=pk)

        try:
            term_months = int(term_months)
            if term_months <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, 'Invalid loan term selected.')
            return redirect('staff:create_loan', pk=pk)

        monthly_rate = interest_rate / 100 / term_months
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / (
                    (1 + monthly_rate) ** term_months - 1)
        total_interest = (monthly_payment * term_months) - principal
        total_payable = principal + total_interest

        loan = Loan.objects.create(
            loan_number=loan_number,
            application=application,
            borrower=application.member,
            loan_product=application.loan_product,
            principal_amount=principal,
            interest_rate=interest_rate,
            term_months=term_months,  # ADD THIS LINE - this fixes the error
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            total_payable_amount=total_payable,
            remaining_balance=principal,
            disbursement_date=date.today(),
            due_date=date.today() + timedelta(days=term_months * 30),
            next_due_date=date.today() + timedelta(days=30),
            status='active'
        )

        application.status = 'disbursed'
        application.save()

        messages.success(request, f'Loan {loan_number} created and disbursed successfully!')
        return redirect('staff:staff_loans')

    # GET request - show the form with term selection
    context = {
        'staff_profile': staff_profile,
        'application': application,
        'principal': float(application.approved_line) if application.approved_line else 0,
        'interest_rate': float(application.loan_product.interest_rate) if application.loan_product else 15,
        'total_deductions': float(application.total_deductions) if application.total_deductions else 0,
        'net_proceeds': float(application.net_proceeds) if application.net_proceeds else 0,
    }

    return render(request, 'staff/applications/create_loan.html', context)

def create_payments(loans):
    """Create payment records for loans"""
    print(f"\n💵 Creating payment records...")

    payment_methods = ['cash', 'cash', 'cash', 'quedan', 'pesada']
    total_payments = 0

    for loan in loans:
        if loan.status == 'paid':
            num_payments = 12
        elif loan.status == 'active':
            num_payments = random.randint(1, 6)
        elif loan.status == 'overdue':
            num_payments = random.randint(1, 4)
        else:
            num_payments = 0

        for k in range(num_payments):
            payment_date = loan.disbursement_date + timedelta(days=(k + 1) * 30)
            if payment_date > date.today():
                payment_date = date.today() - timedelta(days=random.randint(1, 30))

            amount = float(loan.monthly_payment)
            if k == num_payments - 1 and loan.status == 'paid':
                amount = float(loan.remaining_balance + loan.monthly_payment)

            method = random.choice(payment_methods)

            payment, created = Payment.objects.get_or_create(
                loan=loan,
                payment_date=payment_date,
                defaults={
                    'member': loan.borrower,
                    'amount': amount,
                    'payment_method': method,
                    'is_posted': True,
                    'posted_at': payment_date,
                    'principal_amount': amount * 0.8,
                    'interest_amount': amount * 0.2,
                    'penalty_amount': 0
                }
            )
            if created:
                total_payments += 1

    print(f"  ✅ Total payments created: {total_payments}")


def generate_summary():
    """Generate summary of created data"""
    print("\n" + "=" * 70)
    print("📊 DATA SUMMARY")
    print("=" * 70)

    # User counts
    print(f"\n👥 USER ACCOUNTS:")
    print(f"  • Total Users: {User.objects.count()}")
    print(f"  • Staff Members: {User.objects.filter(is_staff=True, is_superuser=False).count()}")
    print(f"  • Super Users: {User.objects.filter(is_superuser=True).count()}")

    # Member stats
    print(f"\n👤 MEMBERS:")
    print(f"  • Total Members: {Member.objects.count()}")
    print(f"  • Active Members: {Member.objects.filter(is_active=True).count()}")
    print(f"  • Employee Members: {Member.objects.filter(is_employee=True).count()}")
    print(f"  • Farmer Members: {Member.objects.filter(is_employee=False).count()}")

    # Application stats
    print(f"\n📋 LOAN APPLICATIONS:")
    print(f"  • Total Applications: {LoanApplication.objects.count()}")
    print(f"  • Pending Review: {LoanApplication.objects.filter(status='pending_staff_review').count()}")
    print(f"  • With Committee: {LoanApplication.objects.filter(status='with_committee').count()}")
    print(f"  • Line Approved: {LoanApplication.objects.filter(status='line_approved').count()}")
    print(f"  • Manager Approved: {LoanApplication.objects.filter(status='manager_approved').count()}")
    print(f"  • Rejected: {LoanApplication.objects.filter(status='rejected').count()}")

    # Loan stats
    print(f"\n💰 LOANS:")
    print(f"  • Total Loans: {Loan.objects.count()}")
    print(f"  • Active Loans: {Loan.objects.filter(status='active').count()}")
    print(f"  • Overdue Loans: {Loan.objects.filter(status='overdue').count()}")
    print(f"  • Paid Loans: {Loan.objects.filter(status='paid').count()}")
    print(f"  • Restructured Loans: {Loan.objects.filter(status='restructured').count()}")

    # Loan by type
    print(f"\n📊 LOANS BY TYPE:")
    for loan_type in LOAN_TYPES.keys():
        count = Loan.objects.filter(loan_type=loan_type).count()
        total_amount = Loan.objects.filter(loan_type=loan_type).aggregate(total=models.Sum('principal_amount'))[
                           'total'] or 0
        if count > 0:
            print(f"  • {loan_type}: {count} loans - ₱{total_amount:,.2f}")

    # Payment stats
    print(f"\n💵 PAYMENTS:")
    print(f"  • Total Payments: {Payment.objects.count()}")
    total_amount = Payment.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    print(f"  • Total Collection: ₱{total_amount:,.2f}")

    print("\n" + "=" * 70)
    print("✅ SAMPLE DATA CREATION COMPLETE!")
    print("=" * 70)

    print("\n🔑 LOGIN CREDENTIALS:")
    print("-" * 50)
    print("  STAFF (Loan Officers):")
    print("    Username: juan.dela.cruz / staff123")
    print("    Username: maria.santos / staff123")
    print("    Username: pedro.reyes / staff123")
    print("    Username: ana.lim / staff123")
    print("\n  COMMITTEE:")
    print("    Username: antonio.fernandez / committee123")
    print("    Username: carmen.garcia / committee123")
    print("    Username: ricardo.mendoza / committee123")
    print("\n  MANAGER:")
    print("    Username: roberto.villanueva / manager123")
    print("\n  CASHIER:")
    print("    Username: analiza.reyes / cashier123")
    print("    Username: jose.martinez / cashier123")
    print("\n  MEMBER (sample):")
    print("    Username: [first_name].[last_name] / member123")
    print("    Example: juan.delacruz / member123")
    print("=" * 70)


def main():
    print("\n" + "🏦" * 35)
    print("TOMPuCO LOAN MANAGEMENT SYSTEM")
    print("COMPREHENSIVE SAMPLE DATA CREATION")
    print("🏦" * 35)

    try:
        create_users()
        members = create_members()
        applications = create_loan_applications(members)
        loans = create_loans(members)
        create_payments(loans)
        generate_summary()

        print("\n🎉 All sample data has been created successfully!")
        print("You can now login and test all features.\n")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("Please make sure all models are properly set up.")


if __name__ == "__main__":
    import django
    import sys

    main()