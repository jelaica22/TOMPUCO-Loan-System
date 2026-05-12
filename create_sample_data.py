import os
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.utils import timezone
from main.models import (
    Member, Loan, LoanApplication, LoanProduct,
    Payment, PaymentSchedule, Notification, SystemSetting
)


def create_groups():
    """Create user groups"""
    groups = ['Staff', 'Manager', 'Cashier', 'Committee']
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"✓ Created group: {group_name}")


def create_admin():
    """Create super admin user"""
    if not User.objects.filter(username='superadmin').exists():
        admin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@tompuco.com',
            password='Admin@123456',
            first_name='System',
            last_name='Administrator'
        )
        admin.save()
        print("✓ Created Super Admin: superadmin / Admin@123456")
    return True


def create_staff_members():
    """Create staff members (users with staff access)"""
    staff_data = [
        {'username': 'staff.juan', 'email': 'juan@tompuco.com', 'first_name': 'Juan', 'last_name': 'Dela Cruz',
         'contact': '09123456789', 'gender': 'M'},
        {'username': 'staff.maria', 'email': 'maria@tompuco.com', 'first_name': 'Maria', 'last_name': 'Santos',
         'contact': '09123456790', 'gender': 'F'},
        {'username': 'staff.pedro', 'email': 'pedro@tompuco.com', 'first_name': 'Pedro', 'last_name': 'Reyes',
         'contact': '09123456791', 'gender': 'M'},
    ]

    for data in staff_data:
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='Staff@123456',
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_staff=True
            )
            user.save()

            staff_group, _ = Group.objects.get_or_create(name='Staff')
            user.groups.add(staff_group)
            print(f"✓ Created staff: {data['username']}")


def create_manager_members():
    """Create manager users"""
    manager_data = [
        {'username': 'manager.maria', 'email': 'maria.manager@tompuco.com', 'first_name': 'Maria',
         'last_name': 'Villanueva', 'contact': '09123456793', 'gender': 'F'},
        {'username': 'manager.ricardo', 'email': 'ricardo.manager@tompuco.com', 'first_name': 'Ricardo',
         'last_name': 'Dizon', 'contact': '09123456794', 'gender': 'M'},
    ]

    for data in manager_data:
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='Manager@123456',
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_staff=True
            )
            user.save()

            manager_group, _ = Group.objects.get_or_create(name='Manager')
            user.groups.add(manager_group)
            print(f"✓ Created manager: {data['username']}")


def create_cashier_members():
    """Create cashier users"""
    cashier_data = [
        {'username': 'cashier.carla', 'email': 'carla@tompuco.com', 'first_name': 'Carla', 'last_name': 'Fernandez',
         'contact': '09123456795', 'gender': 'F'},
    ]

    for data in cashier_data:
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='Cashier@123456',
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_staff=True
            )
            user.save()

            cashier_group, _ = Group.objects.get_or_create(name='Cashier')
            user.groups.add(cashier_group)
            print(f"✓ Created cashier: {data['username']}")


def create_committee_members():
    """Create committee users"""
    committee_data = [
        {'username': 'committee.alicia', 'email': 'alicia@tompuco.com', 'first_name': 'Alicia', 'last_name': 'Gonzales',
         'contact': '09123456797', 'gender': 'F'},
    ]

    for data in committee_data:
        if not User.objects.filter(username=data['username']).exists():
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='Committee@123456',
                first_name=data['first_name'],
                last_name=data['last_name'],
                is_staff=True
            )
            user.save()

            committee_group, _ = Group.objects.get_or_create(name='Committee')
            user.groups.add(committee_group)
            print(f"✓ Created committee: {data['username']}")


def create_regular_members():
    """Create regular (non-employee) members"""
    members_data = [
        {'first_name': 'Jesus', 'last_name': 'Parreno', 'address': 'Villareal, Bayawan City', 'income': 25000,
         'contact': '09123456001', 'gender': 'M'},
        {'first_name': 'Riza', 'last_name': 'Duran', 'address': 'Nangka, Bayawan City', 'income': 35000,
         'contact': '09123456003', 'gender': 'F'},
        {'first_name': 'Michael', 'last_name': 'Tan', 'address': 'San Jose, Bayawan City', 'income': 28000,
         'contact': '09123456004', 'gender': 'M'},
        {'first_name': 'Ramon', 'last_name': 'Cruz', 'address': 'Tayawan, Bayawan City', 'income': 45000,
         'contact': '09123456006', 'gender': 'M'},
        {'first_name': 'Luz', 'last_name': 'Mercado', 'address': 'Bating, Bayawan City', 'income': 22000,
         'contact': '09123456007', 'gender': 'F'},
    ]

    created_members = []
    for data in members_data:
        username = f"member.{data['first_name'].lower()}.{data['last_name'].lower()}"
        email = f"{data['first_name'].lower()}.{data['last_name'].lower()}@member.com"

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password='Member@123456',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            user.save()

            membership_number = f"M-{random.randint(10000, 99999)}"
            member = Member.objects.create(
                user=user,
                membership_number=membership_number,
                first_name=data['first_name'],
                last_name=data['last_name'],
                middle_initial=random.choice(['', 'A', 'B', 'C']),
                contact_number=data['contact'],
                residence_address=data['address'],
                monthly_income=data['income'],
                is_employee=False,
                is_active=True,
                age=random.randint(25, 60),
                gender=data['gender'],
                nationality='Filipino',
                years_in_address=random.randint(1, 20),
                years_in_community=random.randint(1, 20),
            )
            created_members.append(member)
            print(f"✓ Created regular member: {username} (ID: {membership_number})")

    return created_members


def create_employee_members():
    """Create employee members (with employee details)"""
    employees_data = [
        {'first_name': 'Grace', 'last_name': 'Pao', 'address': 'Kalumboyan, Bayawan City', 'monthly_income': 30000,
         'contact': '09123456002', 'gender': 'F',
         'employer': 'Department of Education', 'position': 'Teacher', 'monthly_salary': 30000},
        {'first_name': 'Catherine', 'last_name': 'Lim', 'address': 'Dawis, Bayawan City', 'monthly_income': 32000,
         'contact': '09123456005', 'gender': 'F',
         'employer': 'Bayawan City Hospital', 'position': 'Nurse', 'monthly_salary': 32000},
        {'first_name': 'Felipe', 'last_name': 'Reyes', 'address': 'Villareal, Bayawan City', 'monthly_income': 38000,
         'contact': '09123456008', 'gender': 'M',
         'employer': 'LGU Bayawan', 'position': 'Government Employee', 'monthly_salary': 38000},
        {'first_name': 'Andrea', 'last_name': 'Villanueva', 'address': 'Tayawan, Bayawan City', 'monthly_income': 42000,
         'contact': '09123456011', 'gender': 'F',
         'employer': 'PNP', 'position': 'Police Officer', 'monthly_salary': 42000},
        {'first_name': 'Benjamin', 'last_name': 'Fernandez', 'address': 'Kalumboyan, Bayawan City',
         'monthly_income': 35000, 'contact': '09123456012', 'gender': 'M',
         'employer': 'DOLE', 'position': 'OFW', 'monthly_salary': 35000},
    ]

    created_members = []
    for data in employees_data:
        username = f"employee.{data['first_name'].lower()}.{data['last_name'].lower()}"
        email = f"{data['first_name'].lower()}.{data['last_name'].lower()}@employee.com"

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password='Employee@123456',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            user.save()

            membership_number = f"M-{random.randint(10000, 99999)}"
            member = Member.objects.create(
                user=user,
                membership_number=membership_number,
                first_name=data['first_name'],
                last_name=data['last_name'],
                middle_initial=random.choice(['', 'D', 'E', 'F']),
                contact_number=data['contact'],
                residence_address=data['address'],
                monthly_income=data['monthly_income'],
                is_employee=True,
                employer_name=data['employer'],
                position=data['position'],
                monthly_salary=data['monthly_salary'],
                is_active=True,
                age=random.randint(25, 55),
                gender=data['gender'],
                nationality='Filipino',
                years_in_address=random.randint(1, 15),
                years_in_community=random.randint(1, 15),
            )
            created_members.append(member)
            print(f"✓ Created employee member: {username} (ID: {membership_number}, Employer: {data['employer']})")

    return created_members


def create_loan_products():
    """Create loan products"""
    products = [
        {'name': 'APCP', 'display_name': 'Agricultural Production Credit', 'interest_rate': 15, 'term_months': 12,
         'min_amount': 10000, 'max_amount': 200000},
        {'name': 'NCL', 'display_name': 'Non-Collateralized Loan', 'interest_rate': 20, 'term_months': 12,
         'min_amount': 5000, 'max_amount': 100000},
        {'name': 'SALARY', 'display_name': 'Salary Loan', 'interest_rate': 8, 'term_months': 12, 'min_amount': 5000,
         'max_amount': 50000},
        {'name': 'COLLATERAL', 'display_name': 'Collateral Loan', 'interest_rate': 18, 'term_months': 24,
         'min_amount': 50000, 'max_amount': 500000},
        {'name': 'PROVIDENTIAL', 'display_name': 'Providential Loan', 'interest_rate': 16, 'term_months': 12,
         'min_amount': 10000, 'max_amount': 150000},
    ]

    created_products = []
    for data in products:
        product, created = LoanProduct.objects.get_or_create(
            name=data['name'],
            defaults={
                'display_name': data['display_name'],
                'interest_rate': Decimal(str(data['interest_rate'])),
                'term_months': data['term_months'],
                'term_days': data['term_months'] * 30,
                'min_amount': data['min_amount'],
                'max_amount': data['max_amount'],
                'is_active': True
            }
        )
        created_products.append(product)
        if created:
            print(f"✓ Created loan product: {data['name']}")

    return created_products


def create_loan_applications(members, products):
    """Create loan applications"""
    statuses = ['pending_staff_review', 'with_committee', 'line_approved', 'manager_approved', 'rejected',
                'needs_revision']
    purposes = [
        'Agricultural input purchase', 'Business expansion', 'Home renovation',
        'Education expenses', 'Medical emergency', 'Farm equipment upgrade',
        'Livestock purchase', 'School fees', 'House repair', 'Startup capital'
    ]

    applications = []
    for i, member in enumerate(members[:12]):
        # Employees can apply for Salary Loan, regular members cannot
        if member.is_employee:
            available_products = products
        else:
            available_products = [p for p in products if p.name != 'SALARY']

        if not available_products:
            continue

        product = random.choice(available_products)
        requested_amount = random.randint(int(product.min_amount), int(product.max_amount))
        status = random.choice(statuses)

        application_id = f"{product.name}-{datetime.now().year}-{random.randint(1000, 9999)}"

        app = LoanApplication.objects.create(
            application_id=application_id,
            member=member,
            loan_product=product,
            requested_amount=requested_amount,
            purpose=random.choice(purposes),
            status=status,
            applicant_user=member.user,
            created_at=timezone.now() - timedelta(days=random.randint(1, 60))
        )

        if status in ['line_approved', 'manager_approved']:
            app.approved_line = requested_amount * Decimal('0.9')
            app.net_proceeds = app.approved_line * Decimal('1.0532') + 235
            app.save()

        applications.append(app)
        member_type = "Employee" if member.is_employee else "Regular"
        print(f"✓ Created {member_type} application: {application_id}")

    return applications


def create_loans(applications):
    """Create actual loans from approved applications"""
    loans = []
    approved_apps = [app for app in applications if app.status == 'manager_approved']

    for i, app in enumerate(approved_apps[:8]):
        year = datetime.now().year
        loan_number = f"LN-{year}-{1000 + i}"

        # Calculate monthly payment
        principal = app.approved_line
        interest_rate = app.loan_product.interest_rate / 100
        term_months = app.loan_product.term_months

        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / (
                    (1 + monthly_rate) ** term_months - 1)
        else:
            monthly_payment = principal / term_months

        # Calculate total interest and total payable
        total_interest = (monthly_payment * term_months) - principal
        total_payable = monthly_payment * term_months
        net_proceeds = app.approved_line * Decimal('1.0532') + 235

        # Create loan with reference to the application
        loan = Loan.objects.create(
            loan_number=loan_number,
            application=app,  # Link to the application (foreign key)
            borrower=app.member,
            loan_product=app.loan_product,
            principal_amount=app.approved_line,
            remaining_balance=app.approved_line,
            interest_rate=app.loan_product.interest_rate,
            term_months=app.loan_product.term_months,
            disbursement_date=timezone.now().date() - timedelta(days=random.randint(10, 90)),
            due_date=timezone.now().date() + timedelta(days=app.loan_product.term_months * 30),
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            total_payable_amount=total_payable,
            net_proceeds=net_proceeds,
            status='active'
        )

        # Update application
        app.funded_loan = loan
        app.status = 'ready_for_disbursement'
        app.save()

        loans.append(loan)
        print(f"✓ Created loan: {loan_number}")

    return loans


def create_payment_schedules(loans):
    """Create payment schedules for loans"""
    schedules = []
    for loan in loans:
        PaymentSchedule.objects.filter(loan=loan).delete()

        principal = loan.principal_amount
        interest_rate = loan.interest_rate / 100
        term_months = loan.term_months

        monthly_rate = interest_rate / 12
        if monthly_rate > 0:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / (
                    (1 + monthly_rate) ** term_months - 1)
        else:
            monthly_payment = principal / term_months

        remaining_balance = principal
        current_date = loan.disbursement_date or timezone.now().date()

        for month in range(1, term_months + 1):
            interest_due = remaining_balance * monthly_rate
            principal_due = monthly_payment - interest_due
            due_date = current_date + timedelta(days=30 * month)

            schedule = PaymentSchedule.objects.create(
                loan=loan,
                schedule_number=month,
                due_date=due_date,
                principal_due=principal_due,
                interest_due=interest_due,
                penalty_due=0,
                total_due=monthly_payment,
                status='pending'
            )
            schedules.append(schedule)
            remaining_balance -= principal_due

        print(f"✓ Created {term_months} payment schedules for loan {loan.loan_number}")

    return schedules


def create_payments(loans):
    """Create payments for loans"""
    payments = []
    payment_methods = ['cash', 'quedan', 'pesada']

    for loan in loans[:6]:
        payment_count = random.randint(1, 3)
        for i in range(payment_count):
            year = datetime.now().year
            payment_number = f"PAY-{year}-{random.randint(100000, 999999)}"

            amount = random.randint(2000, 8000)
            loan.remaining_balance -= amount
            if loan.remaining_balance < 0:
                loan.remaining_balance = 0

            payment = Payment.objects.create(
                payment_number=payment_number,
                loan=loan,
                member=loan.borrower,
                amount=amount,
                payment_date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                payment_method=random.choice(payment_methods),
                status='completed'
            )
            payments.append(payment)

        loan.save()
        print(f"✓ Created {payment_count} payments for loan {loan.loan_number}")

    return payments


def create_notifications(users):
    """Create notifications"""
    titles = [
        'Application Submitted', 'Payment Received', 'Application Approved',
        'Loan Disbursed', 'Document Required', 'Committee Decision'
    ]
    messages = [
        'Your loan application has been submitted for review.',
        'Your payment has been successfully processed.',
        'Congratulations! Your loan application has been approved.',
        'Your loan has been disbursed to your account.',
        'Please submit additional documents for your application.',
        'The committee has reviewed your application.'
    ]

    notifications = []
    for user in users[:20]:
        for i in range(random.randint(1, 2)):
            notif = Notification.objects.create(
                recipient=user,
                title=random.choice(titles),
                message=random.choice(messages),
                is_read=random.choice([True, False]),
                notification_type='info',
                created_at=timezone.now() - timedelta(days=random.randint(1, 15))
            )
            notifications.append(notif)

    print(f"✓ Created {len(notifications)} notifications")


def create_system_settings():
    """Create system settings"""
    settings = [
        {'key': 'interest_rate_default', 'value': '20', 'description': 'Default interest rate'},
        {'key': 'penalty_rate', 'value': '2', 'description': 'Monthly penalty rate'},
        {'key': 'service_charge_rate', 'value': '3', 'description': 'Service charge percentage'},
        {'key': 'insurance_rate', 'value': '1.32', 'description': 'Insurance charge percentage'},
        {'key': 'cbu_retention_rate', 'value': '2', 'description': 'CBU retention percentage'},
    ]

    for data in settings:
        setting, created = SystemSetting.objects.get_or_create(
            setting_key=data['key'],
            defaults={
                'setting_value': data['value'],
                'description': data['description'],
                'updated_at': timezone.now()
            }
        )
        if created:
            print(f"✓ Created setting: {data['key']}")


def main():
    print("\n" + "=" * 60)
    print("STARTING SAMPLE DATA CREATION")
    print("=" * 60 + "\n")

    # Create groups
    create_groups()

    # Create staff/manager/cashier/committee users
    create_admin()
    create_staff_members()
    create_manager_members()
    create_cashier_members()
    create_committee_members()

    # Create members (regular and employees)
    regular_members = create_regular_members()
    employee_members = create_employee_members()
    all_members = regular_members + employee_members

    # Create system settings
    create_system_settings()

    # Create loan products
    products = create_loan_products()

    # Create loan applications
    applications = create_loan_applications(all_members, products)

    # Create loans from approved applications
    loans = create_loans(applications)

    # Create payment schedules
    schedules = create_payment_schedules(loans)

    # Create payments
    payments = create_payments(loans)

    # Create notifications
    all_users = list(User.objects.all())
    create_notifications(all_users)

    print("\n" + "=" * 60)
    print("SAMPLE DATA CREATION COMPLETE!")
    print("=" * 60)
    print(f"\n📊 SUMMARY:")
    print(f"  • Total Users: {User.objects.count()}")
    print(f"  • Regular Members: {Member.objects.filter(is_employee=False).count()}")
    print(f"  • Employee Members: {Member.objects.filter(is_employee=True).count()}")
    print(f"  • Loan Products: {LoanProduct.objects.count()}")
    print(f"  • Loan Applications: {LoanApplication.objects.count()}")
    print(f"  • Loans: {Loan.objects.count()}")
    print(f"  • Payment Schedules: {PaymentSchedule.objects.count()}")
    print(f"  • Payments: {Payment.objects.count()}")
    print(f"  • Notifications: {Notification.objects.count()}")
    print(f"  • System Settings: {SystemSetting.objects.count()}")

    print("\n🔐 LOGIN CREDENTIALS:")
    print("  • Super Admin: superadmin / Admin@123456")
    print("  • Manager: manager.maria / Manager@123456")
    print("  • Staff: staff.juan / Staff@123456")
    print("  • Cashier: cashier.carla / Cashier@123456")
    print("  • Committee: committee.alicia / Committee@123456")
    print("  • Regular Member: member.jesus.parreno / Member@123456")
    print("  • Employee Member: employee.grace.pao / Employee@123456")


if __name__ == '__main__':
    main()