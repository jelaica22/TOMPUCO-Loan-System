# create_sample_data.py
import os
import django
from datetime import datetime, timedelta, date
import random
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from main.models import Member, Loan, LoanApplication, Payment
from staff.models import StaffProfile
from committee.models import CommitteeProfile
from cashier.models import CashierProfile
from manager.models import ManagerProfile
from payments.models import Payment as PaymentModel


def create_sample_data():
    print("=" * 70)
    print("🏦 TOMPuCO LOAN MANAGEMENT SYSTEM - SAMPLE DATA CREATION")
    print("=" * 70)

    # ==================== CREATE USERS ====================
    print("\n👥 Creating users for all roles...")

    users_data = [
        # Super Admin
        {'username': 'admin', 'password': 'admin123', 'first_name': 'Admin', 'last_name': 'User',
         'email': 'admin@tompuco.com', 'is_superuser': True, 'is_staff': True},

        # Staff Members (Loan Officers)
        {'username': 'juan.dela.cruz', 'password': 'staff123', 'first_name': 'Juan', 'last_name': 'Dela Cruz',
         'email': 'juan@tompuco.com', 'is_staff': True},
        {'username': 'maria.santos', 'password': 'staff123', 'first_name': 'Maria', 'last_name': 'Santos',
         'email': 'maria@tompuco.com', 'is_staff': True},
        {'username': 'pedro.reyes', 'password': 'staff123', 'first_name': 'Pedro', 'last_name': 'Reyes',
         'email': 'pedro@tompuco.com', 'is_staff': True},

        # Committee Members
        {'username': 'antonio.fernandez', 'password': 'committee123', 'first_name': 'Antonio', 'last_name': 'Fernandez',
         'email': 'antonio@tompuco.com', 'is_staff': True},
        {'username': 'carmen.garcia', 'password': 'committee123', 'first_name': 'Carmen', 'last_name': 'Garcia',
         'email': 'carmen@tompuco.com', 'is_staff': True},
        {'username': 'ricardo.mendoza', 'password': 'committee123', 'first_name': 'Ricardo', 'last_name': 'Mendoza',
         'email': 'ricardo@tompuco.com', 'is_staff': True},

        # Manager
        {'username': 'roberto.villanueva', 'password': 'manager123', 'first_name': 'Roberto', 'last_name': 'Villanueva',
         'email': 'roberto@tompuco.com', 'is_staff': True, 'is_superuser': True},

        # Cashier
        {'username': 'analiza.reyes', 'password': 'cashier123', 'first_name': 'Analiza', 'last_name': 'Reyes',
         'email': 'analiza@tompuco.com', 'is_staff': True},
        {'username': 'jose.martinez', 'password': 'cashier123', 'first_name': 'Jose', 'last_name': 'Martinez',
         'email': 'jose@tompuco.com', 'is_staff': True},
    ]

    created_users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'email': user_data['email'],
                'password': make_password(user_data['password']),
                'is_staff': user_data.get('is_staff', False),
                'is_superuser': user_data.get('is_superuser', False),
                'is_active': True
            }
        )
        if created:
            print(f"  ✅ Created: {user_data['username']} / {user_data['password']}")
        else:
            # Update password if needed
            user.set_password(user_data['password'])
            user.save()
            print(f"  🔄 Updated: {user_data['username']} / {user_data['password']}")
        created_users[user_data['username']] = user

    # ==================== CREATE STAFF PROFILES ====================
    print("\n👔 Creating Staff Profiles...")

    staff_positions = ['loan_officer', 'collections_officer', 'credit_investigator']
    for i, username in enumerate(['juan.dela.cruz', 'maria.santos', 'pedro.reyes']):
        user = created_users.get(username)
        if user:
            profile, created = StaffProfile.objects.get_or_create(
                user=user,
                defaults={
                    'staff_id': f"STF{100 + i}",
                    'position': staff_positions[i % len(staff_positions)],
                    'department': 'Loans Department',
                    'hire_date': date(2023, 1, 1),
                    'is_active': True
                }
            )
            print(f"  ✅ Staff Profile: {username} - {profile.position}")

    # ==================== CREATE COMMITTEE PROFILES ====================
    print("\n🏛️ Creating Committee Profiles...")

    committee_positions = ['chairperson', 'member', 'secretary']
    for i, username in enumerate(['antonio.fernandez', 'carmen.garcia', 'ricardo.mendoza']):
        user = created_users.get(username)
        if user:
            profile, created = CommitteeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'committee_id': f"COM{100 + i}",
                    'position': committee_positions[i % len(committee_positions)],
                    'term_start': date(2024, 1, 1),
                    'term_end': date(2026, 12, 31),
                    'is_active': True
                }
            )
            print(f"  ✅ Committee Profile: {username} - {profile.position}")

    # ==================== CREATE MANAGER PROFILE ====================
    print("\n📊 Creating Manager Profile...")

    user = created_users.get('roberto.villanueva')
    if user:
        profile, created = ManagerProfile.objects.get_or_create(
            user=user,
            defaults={
                'manager_id': 'MGR001',
                'position': 'general_manager',
                'department': 'Management',
                'hire_date': date(2022, 1, 1),
                'is_active': True
            }
        )
        print(f"  ✅ Manager Profile: roberto.villanueva - General Manager")

    # ==================== CREATE CASHIER PROFILES ====================
    print("\n💰 Creating Cashier Profiles...")

    for i, username in enumerate(['analiza.reyes', 'jose.martinez']):
        user = created_users.get(username)
        if user:
            profile, created = CashierProfile.objects.get_or_create(
                user=user,
                defaults={
                    'cashier_id': f'CSH{100 + i}',
                    'position': 'cashier',
                    'branch': 'Main Branch',
                    'hire_date': date(2023, 6, 1),
                    'is_active': True
                }
            )
            print(f"  ✅ Cashier Profile: {username}")

    # ==================== CREATE MEMBERS ====================
    print("\n👤 Creating Members...")

    members_data = [
        # Regular Members
        {'first_name': 'Juan', 'last_name': 'Dela Cruz', 'membership_number': 'M-2025-001', 'contact': '09123456789',
         'address': 'Brgy. Villareal, Bayawan City', 'is_employee': False, 'username': 'juan.delacruz',
         'password': 'member123'},
        {'first_name': 'Maria', 'last_name': 'Santos', 'membership_number': 'M-2025-002', 'contact': '09123456788',
         'address': 'Brgy. Kalumboyan, Bayawan City', 'is_employee': True, 'username': 'maria.santos.member',
         'password': 'member123'},
        {'first_name': 'Pedro', 'last_name': 'Reyes', 'membership_number': 'M-2025-003', 'contact': '09123456787',
         'address': 'Brgy. Nangka, Bayawan City', 'is_employee': False, 'username': 'pedro.reyes',
         'password': 'member123'},
        {'first_name': 'Ana', 'last_name': 'Lim', 'membership_number': 'M-2025-004', 'contact': '09123456786',
         'address': 'Brgy. Balabag, Bayawan City', 'is_employee': True, 'username': 'ana.lim', 'password': 'member123'},
        {'first_name': 'Ramon', 'last_name': 'Garcia', 'membership_number': 'M-2025-005', 'contact': '09123456785',
         'address': 'Brgy. San Jose, Bayawan City', 'is_employee': False, 'username': 'ramon.garcia',
         'password': 'member123'},

        # Farmer Members
        {'first_name': 'Cristina', 'last_name': 'Fernandez', 'membership_number': 'M-2025-006',
         'contact': '09123456784',
         'address': 'Brgy. Suba, Bayawan City', 'is_employee': False, 'farm_location': 'Purok 1, Suba',
         'username': 'cristina.fernandez', 'password': 'member123'},
        {'first_name': 'Jose', 'last_name': 'Mendoza', 'membership_number': 'M-2025-007', 'contact': '09123456783',
         'address': 'Brgy. Canlargo, Bayawan City', 'is_employee': False, 'farm_location': 'Sitio Upper Canlargo',
         'username': 'jose.mendoza', 'password': 'member123'},
        {'first_name': 'Elena', 'last_name': 'Villanueva', 'membership_number': 'M-2025-008', 'contact': '09123456782',
         'address': 'Brgy. Malabugas, Bayawan City', 'is_employee': True, 'employer_name': 'DepEd Bayawan',
         'username': 'elena.villanueva', 'password': 'member123'},
        {'first_name': 'Francisco', 'last_name': 'Ramirez', 'membership_number': 'M-2025-009', 'contact': '09123456781',
         'address': 'Brgy. Tinago, Bayawan City', 'is_employee': False, 'farm_location': 'Hacienda Ramirez',
         'username': 'francisco.ramirez', 'password': 'member123'},
        {'first_name': 'Luzviminda', 'last_name': 'Torres', 'membership_number': 'M-2025-010', 'contact': '09123456780',
         'address': 'Brgy. Poblacion, Bayawan City', 'is_employee': True, 'employer_name': 'Bayawan City Hall',
         'username': 'luzviminda.torres', 'password': 'member123'},
    ]

    members = []
    for m_data in members_data:
        # Create user account for member
        user, user_created = User.objects.get_or_create(
            username=m_data['username'],
            defaults={
                'first_name': m_data['first_name'],
                'last_name': m_data['last_name'],
                'email': f"{m_data['first_name'].lower()}.{m_data['last_name'].lower()}@example.com",
                'password': make_password(m_data['password'])
            }
        )

        if user_created:
            print(f"  ✅ Created user account: {m_data['username']} / {m_data['password']}")

        # Create member profile
        member, created = Member.objects.get_or_create(
            membership_number=m_data['membership_number'],
            defaults={
                'user': user,
                'first_name': m_data['first_name'],
                'last_name': m_data['last_name'],
                'contact_number': m_data['contact'],
                'residence_address': m_data['address'],
                'is_employee': m_data.get('is_employee', False),
                'farm_location': m_data.get('farm_location', ''),
                'employer_name': m_data.get('employer_name', ''),
                'is_active': True
            }
        )

        if created:
            print(f"  ✅ Created Member: {member.first_name} {member.last_name} ({member.membership_number})")
        members.append(member)

    # ==================== CREATE LOAN APPLICATIONS ====================
    print("\n📋 Creating Loan Applications...")

    loan_types = ['APCP', 'NCL', 'SALARY', 'COLLATERAL', 'B2B', 'PROVIDENTIAL', 'TRADE']
    statuses = ['pending_staff_review', 'with_committee', 'line_approved', 'manager_approved', 'rejected']

    for i, member in enumerate(members[:8]):
        for j in range(random.randint(0, 2)):
            app_number = f"APCP-2026-{1000 + i * 10 + j}"

            app, created = LoanApplication.objects.get_or_create(
                application_id=app_number,
                defaults={
                    'member': member,
                    'loan_type': random.choice(loan_types),
                    'requested_amount': random.randint(30000, 150000),
                    'purpose': 'Farm improvement and crop production',
                    'collateral': 'Farm land and equipment',
                    'status': random.choice(statuses),
                    'date_applied': date.today() - timedelta(days=random.randint(1, 90))
                }
            )
            if created:
                print(f"  ✅ Created Application: {app_number} - ₱{app.requested_amount:,.2f}")

    # ==================== CREATE LOANS ====================
    print("\n💰 Creating Loan Records...")

    loan_interest_rates = {'APCP': 15, 'NCL': 20, 'SALARY': 8, 'COLLATERAL': 20, 'B2B': 20, 'PROVIDENTIAL': 16,
                           'TRADE': 18}

    for i, member in enumerate(members[:8]):
        for j in range(random.randint(0, 1)):
            loan_type = random.choice(loan_types)
            principal = random.randint(50000, 200000)
            interest_rate = loan_interest_rates[loan_type]

            monthly_rate = interest_rate / 100 / 12
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** 12) / ((1 + monthly_rate) ** 12 - 1)
            total_interest = (monthly_payment * 12) - principal
            total_payable = principal + total_interest

            disbursement_date = date(2025, random.randint(1, 12), random.randint(1, 28))
            status = random.choice(['active', 'active', 'overdue', 'paid'])

            loan_number = f"LN-2025-{1000 + i * 10 + j}"

            loan, created = Loan.objects.get_or_create(
                loan_number=loan_number,
                defaults={
                    'borrower': member,
                    'loan_type': loan_type,
                    'principal_amount': principal,
                    'interest_rate': interest_rate,
                    'monthly_payment': monthly_payment,
                    'total_interest': total_interest,
                    'total_payable': total_payable,
                    'remaining_balance': principal * 0.7,
                    'disbursement_date': disbursement_date,
                    'due_date': disbursement_date + timedelta(days=360),
                    'next_due_date': disbursement_date + timedelta(days=30),
                    'status': status,
                    'paid_amount': principal * 0.3 if status != 'paid' else principal,
                    'last_payment_date': disbursement_date + timedelta(days=30) if status != 'paid' else None
                }
            )
            if created:
                print(f"  ✅ Created Loan: {loan_number} - ₱{principal:,.2f} ({loan_type})")

    # ==================== CREATE PAYMENTS ====================
    print("\n💵 Creating Payment Records...")

    payment_methods = ['cash', 'cash', 'cash', 'quedan', 'pesada']

    for loan in Loan.objects.all()[:15]:
        num_payments = random.randint(1, 6)
        for k in range(num_payments):
            payment_date = loan.disbursement_date + timedelta(days=(k + 1) * 30)
            if payment_date > date.today():
                payment_date = date.today() - timedelta(days=random.randint(1, 30))

            amount = float(loan.monthly_payment)
            method = random.choice(payment_methods)

            payment, created = PaymentModel.objects.get_or_create(
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

    print(f"  ✅ Created Payment Records")

    # ==================== SUMMARY ====================
    print("\n" + "=" * 70)
    print("✅ SAMPLE DATA CREATION COMPLETE!")
    print("=" * 70)

    print("\n📊 DATABASE SUMMARY:")
    print(f"  👥 Total Users: {User.objects.count()}")
    print(f"  👤 Members: {Member.objects.count()}")
    print(f"  👔 Staff: {StaffProfile.objects.count()}")
    print(f"  🏛️ Committee: {CommitteeProfile.objects.count()}")
    print(f"  📊 Manager: {ManagerProfile.objects.count()}")
    print(f"  💰 Cashier: {CashierProfile.objects.count()}")
    print(f"  📋 Applications: {LoanApplication.objects.count()}")
    print(f"  💰 Loans: {Loan.objects.count()}")
    print(f"  💵 Payments: {PaymentModel.objects.count()}")

    print("\n🔑 LOGIN CREDENTIALS:")
    print("-" * 50)
    print("  SUPER ADMIN:")
    print("    Username: admin")
    print("    Password: admin123")
    print("\n  STAFF (Loan Officers):")
    print("    Username: juan.dela.cruz / staff123")
    print("    Username: maria.santos / staff123")
    print("    Username: pedro.reyes / staff123")
    print("\n  COMMITTEE:")
    print("    Username: antonio.fernandez / committee123")
    print("    Username: carmen.garcia / committee123")
    print("    Username: ricardo.mendoza / committee123")
    print("\n  MANAGER:")
    print("    Username: roberto.villanueva / manager123")
    print("\n  CASHIER:")
    print("    Username: analiza.reyes / cashier123")
    print("    Username: jose.martinez / cashier123")
    print("\n  MEMBERS:")
    print("    Username: juan.delacruz / member123")
    print("    Username: maria.santos.member / member123")
    print("    Username: pedro.reyes / member123")
    print("    Username: ana.lim / member123")
    print("    Username: ramon.garcia / member123")
    print("    And more...")
    print("=" * 70)


if __name__ == "__main__":
    create_sample_data()