from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from decimal import Decimal
from datetime import datetime, timedelta, date
import random
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
import json
from django.db import IntegrityError

from main.models import (
    Member, Loan, LoanApplication, LoanProduct,
    Payment, PaymentSchedule, Notification, MemberDocument,
    CommitteeDecision, AuditLog, SystemSetting, PaymentReceipt,
    LoanAttachment
)
from django.contrib.auth.models import User
from staff.models import StaffProfile
from cashier.models import CashierProfile
from committee.models import CommitteeProfile
from manager.models import ManagerProfile
import random


def generate_staff_code():
    return f"STF-{random.randint(1000, 9999)}"


def generate_cashier_code():
    return f"CSH-{random.randint(1000, 9999)}"


def generate_committee_code():
    return f"COM-{random.randint(1000, 9999)}"


def generate_manager_code():
    return f"MGR-{random.randint(1000, 9999)}"


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_staff_user(request):
    """Only superusers can create staff accounts"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        user_type = request.POST.get('user_type')  # staff, cashier, committee, manager, admin

        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('admin_panel:create_staff_user')

        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.is_staff = True

        if user_type == 'admin':
            user.is_superuser = True

        user.save()

        # Create profile based on type
        if user_type == 'staff':
            StaffProfile.objects.create(
                user=user,
                staff_id=generate_staff_code(),  # ✅ FIXED: staff_id
                position='loan_officer',
                is_active=True
            )
            messages.success(request, f"Staff (Loan Officer) account created!")

        elif user_type == 'cashier':
            CashierProfile.objects.create(
                user=user,
                cashier_id=generate_cashier_code(),  # ✅ FIXED: cashier_id
                is_active=True
            )
            messages.success(request, f"Cashier account created!")

        elif user_type == 'committee':
            CommitteeProfile.objects.create(
                user=user,
                committee_id=generate_committee_code(),  # ✅ FIXED: committee_id
                is_active=True
            )
            messages.success(request, f"Committee account created!")

        elif user_type == 'manager':
            ManagerProfile.objects.create(
                user=user,
                manager_id=generate_manager_code(),  # ✅ FIXED: manager_id
                is_active=True
            )
            messages.success(request, f"Manager account created!")

        elif user_type == 'admin':
            messages.success(request, f"Admin account created!")

        return redirect('admin_panel:users_list')

    return render(request, 'admin_panel/create_staff_user.html')


# ==================== HELPER FUNCTIONS ====================

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def _log_audit(user, action, entity_type, entity_id, old_values=None, new_values=None, request=None):
    try:
        audit = AuditLog(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_values=old_values,
            new_values=new_values,
        )
        if request:
            audit.ip_address = get_client_ip(request)
            audit.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        audit.save()
    except Exception as e:
        print(f"Audit log error: {e}")


# ==================== DECORATORS ====================

def super_admin_required(view_func):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='/dashboard/'
    )
    return actual_decorator(view_func)


# ==================== DASHBOARD ====================

@super_admin_required
def dashboard(request):
    total_users = User.objects.count()
    total_members = Member.objects.count()
    total_applications = LoanApplication.objects.count()
    active_loans = Loan.objects.filter(status='active').count()

    total_loan_amount = Loan.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    collection_rate = (total_payments / total_loan_amount * 100) if total_loan_amount > 0 else 0
    loan_products_count = LoanProduct.objects.count()

    recent_users = User.objects.order_by('-date_joined')[:5]

    user_growth_labels = []
    user_growth_data = []
    for i in range(6, -1, -1):
        dt = datetime.now().date() - timedelta(days=i)
        user_growth_labels.append(dt.strftime('%a'))
        count = User.objects.filter(date_joined__date=dt).count()
        user_growth_data.append(count)

    active_members = Member.objects.filter(is_active=True).count()
    inactive_members = Member.objects.filter(is_active=False).count()

    context = {
        'total_users': total_users,
        'total_members': total_members,
        'total_applications': total_applications,
        'active_loans': active_loans,
        'total_loan_amount': total_loan_amount,
        'total_payments': total_payments,
        'collection_rate': round(collection_rate, 1),
        'loan_products_count': loan_products_count,
        'recent_users': recent_users,
        'user_growth_labels': user_growth_labels,
        'user_growth_data': user_growth_data,
        'member_distribution_labels': ['Active Members', 'Inactive Members'],
        'member_distribution_data': [active_members, inactive_members],
    }
    return render(request, 'admin_panel/dashboard.html', context)


def api_activity_feed(request):
    """API endpoint for recent activity feed"""
    try:
        # Get recent admin log entries
        logs = LogEntry.objects.select_related('user').order_by('-action_time')[:10]

        activities = []
        for log in logs:
            activity = {
                'id': log.id,
                'title': log.get_change_message() or log.action_flag,
                'description': f'{log.user.username} {log.get_action_flag_display()} {log.content_type}',
                'icon': 'bi-person-check' if log.action_flag == 1 else 'bi-pencil' if log.action_flag == 2 else 'bi-trash',
                'link': f'/admin/{log.content_type.app_label}/{log.content_type.model}/{log.object_id}/change/',
                'created_at': log.action_time.isoformat()
            }
            activities.append(activity)

        return JsonResponse({'activities': activities})
    except Exception as e:
        return JsonResponse({'activities': [], 'error': str(e)})


# ==================== PROFILE FUNCTIONS ====================

@login_required
def profile(request):
    """Admin profile page"""
    from .models import AdminProfile

    admin_profile, created = AdminProfile.objects.get_or_create(user=request.user)

    days_active = (timezone.now() - request.user.date_joined).days if request.user.date_joined else 0

    context = {
        'admin_profile': admin_profile,
        'total_users': User.objects.count(),
        'total_members': Member.objects.count(),
        'days_active': days_active,
        'recent_logs': AuditLog.objects.filter(user=request.user).order_by('-created_at')[:5],
    }
    return render(request, 'admin_panel/profile.html', context)


@login_required
def update_profile(request):
    """Update user profile information"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', '')
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('admin_panel:profile')

    return redirect('admin_panel:profile')


@login_required
def upload_avatar(request):
    """Upload profile picture"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        from .models import AdminProfile

        admin_profile, created = AdminProfile.objects.get_or_create(user=request.user)

        if admin_profile.profile_picture:
            try:
                admin_profile.profile_picture.delete(save=False)
            except:
                pass

        admin_profile.profile_picture = request.FILES['avatar']
        admin_profile.save()

        messages.success(request, 'Profile picture updated successfully!')
        return redirect('admin_panel:profile')

    messages.error(request, 'No image selected')
    return redirect('admin_panel:profile')


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if not check_password(current, request.user.password):
            messages.error(request, 'Current password is incorrect.')
        elif new != confirm:
            messages.error(request, 'Passwords do not match.')
        elif len(new) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')

        return redirect('admin_panel:profile')

    return redirect('admin_panel:profile')


# ==================== USERS MANAGEMENT ====================

@super_admin_required
def users_list(request):
    """List all users with role filtering"""
    from main.models import Member

    users = User.objects.all().order_by('-date_joined')

    search = request.GET.get('search', '').strip()
    role = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    # Get member user IDs for filtering - FIXED: use employment_status
    member_user_ids = Member.objects.values_list('user_id', flat=True)
    regular_member_ids = Member.objects.filter(employment_status='member').values_list('user_id', flat=True)
    employee_member_ids = Member.objects.filter(employment_status='employee').values_list('user_id', flat=True)

    # Apply role filter
    if role == 'staff':
        users = users.filter(is_staff=True, is_superuser=False)
    elif role == 'superuser':
        users = users.filter(is_superuser=True)
    elif role == 'regular_member':
        users = users.filter(id__in=regular_member_ids)
    elif role == 'employee_member':
        users = users.filter(id__in=employee_member_ids)
    elif role == 'cashier':
        users = users.filter(groups__name='Cashier')
    elif role == 'manager':
        users = users.filter(groups__name='Manager')
    elif role == 'committee':
        users = users.filter(groups__name='Committee')
    elif role == 'normal':
        users = users.filter(is_staff=False, is_superuser=False).exclude(id__in=member_user_ids)

    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    # Calculate counts for stats - FIXED: use employment_status
    staff_count = User.objects.filter(is_staff=True, is_superuser=False).count()
    superuser_count = User.objects.filter(is_superuser=True).count()
    regular_member_count = Member.objects.filter(employment_status='member').count()
    employee_member_count = Member.objects.filter(employment_status='employee').count()
    cashier_count = User.objects.filter(groups__name='Cashier').count()
    manager_count = User.objects.filter(groups__name='Manager').count()
    committee_count = User.objects.filter(groups__name='Committee').count()
    active_count = User.objects.filter(is_active=True).count()
    inactive_count = User.objects.filter(is_active=False).count()
    total_users = User.objects.count()

    # Annotate users with member info for template
    for user in users:
        if hasattr(user, 'member_profile'):
            user.is_regular_member = user.member_profile.employment_status == 'member'
            user.is_employee_member = user.member_profile.employment_status == 'employee'
        else:
            user.is_regular_member = False
            user.is_employee_member = False

    return render(request, 'admin_panel/users_list.html', {
        'users': users,
        'total_users': total_users,
        'staff_count': staff_count,
        'superuser_count': superuser_count,
        'regular_member_count': regular_member_count,
        'employee_member_count': employee_member_count,
        'cashier_count': cashier_count,
        'manager_count': manager_count,
        'committee_count': committee_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
    })


@super_admin_required
def user_detail(request, user_id):
    """Get user details as JSON"""
    user = get_object_or_404(User, id=user_id)
    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
        "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else None,
        "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M"),
    })


@super_admin_required
def user_edit(request, user_id):
    """Edit a user"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        try:
            # Get form data
            email = request.POST.get('email')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            role = request.POST.get('role')
            is_active = request.POST.get('is_active') == 'true'
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')

            # Update user fields (username is preserved from hidden field)
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active

            # Handle role changes
            if role == 'superuser':
                user.is_superuser = True
                user.is_staff = True
                user.groups.clear()
            elif role in ['staff', 'cashier', 'manager', 'committee']:
                user.is_superuser = False
                user.is_staff = True
                user.groups.clear()

                group_map = {
                    'staff': 'Staff',
                    'cashier': 'Cashier',
                    'manager': 'Manager',
                    'committee': 'Committee'
                }
                group_name = group_map.get(role)
                if group_name:
                    group, _ = Group.objects.get_or_create(name=group_name)
                    user.groups.add(group)
            else:  # normal user
                user.is_superuser = False
                user.is_staff = False
                user.groups.clear()

            # Handle password change if provided
            if new_password:
                if new_password == confirm_password and len(new_password) >= 8:
                    user.set_password(new_password)
                    messages.success(request, f'Password updated for {user.username}')
                else:
                    messages.error(request, 'Password mismatch or too short (min 8 characters)')
                    return redirect('admin_panel:user_edit', user_id=user.id)

            # Save the user
            user.save()

            # Update or create member profile
            try:
                member = user.member_profile
                member.first_name = user.first_name or user.username
                member.last_name = user.last_name or ''
                member.is_active = user.is_active
                member.save()
            except:
                Member.objects.create(
                    user=user,
                    first_name=user.first_name or user.username,
                    last_name=user.last_name or '',
                    contact_number='',
                    residence_address='',
                    is_active=user.is_active
                )

            messages.success(request, f'User "{user.username}" has been updated successfully.')
            return redirect('admin_panel:users_list')

        except IntegrityError as e:
            messages.error(request, f'Database error: {str(e)}')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

    return render(request, 'admin_panel/user_edit.html', {'user': user})


@super_admin_required
def user_create(request):
    """Create a new user with role"""
    from main.models import Member
    from django.contrib.auth.models import Group
    from staff.models import StaffProfile
    from cashier.models import CashierProfile
    from committee.models import CommitteeProfile
    from manager.models import ManagerProfile
    import random
    from decimal import Decimal
    from datetime import datetime

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        role = request.POST.get('role', 'normal')
        is_active = request.POST.get('is_active') == 'true'

        # Validation
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active
        )

        # Generate membership number
        def generate_membership_number():
            while True:
                number = f"M-{random.randint(10000, 99999)}"
                if not Member.objects.filter(membership_number=number).exists():
                    return number

        # Generate Employee ID (auto-increment)
        def generate_employee_id():
            year = datetime.now().year
            # Get the last employee ID
            last_employee = Member.objects.filter(
                employment_status='employee',
                employee_id__isnull=False
            ).order_by('-id').first()

            if last_employee and last_employee.employee_id:
                try:
                    # Extract number from format EMP-2024-0001
                    parts = last_employee.employee_id.split('-')
                    if len(parts) >= 3:
                        last_num = int(parts[-1])
                        new_num = last_num + 1
                    else:
                        new_num = 1000
                except (ValueError, IndexError):
                    new_num = 1000
            else:
                new_num = 1000

            return f"EMP-{year}-{new_num:04d}"

        # Generate Staff ID
        def generate_staff_id():
            year = datetime.now().year
            last_staff = StaffProfile.objects.order_by('-id').first()
            if last_staff and last_staff.staff_id:
                try:
                    last_num = int(last_staff.staff_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = random.randint(1000, 9999)
            else:
                new_num = 1000
            return f"STF-{year}-{new_num:04d}"

        # Generate Cashier ID
        def generate_cashier_id():
            year = datetime.now().year
            last_cashier = CashierProfile.objects.order_by('-id').first()
            if last_cashier and last_cashier.cashier_id:
                try:
                    last_num = int(last_cashier.cashier_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = random.randint(1000, 9999)
            else:
                new_num = 1000
            return f"CSH-{year}-{new_num:04d}"

        # Generate Manager ID
        def generate_manager_id():
            year = datetime.now().year
            last_manager = ManagerProfile.objects.order_by('-id').first()
            if last_manager and last_manager.manager_id:
                try:
                    last_num = int(last_manager.manager_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = random.randint(1000, 9999)
            else:
                new_num = 1000
            return f"MGR-{year}-{new_num:04d}"

        # Generate Committee ID
        def generate_committee_id():
            year = datetime.now().year
            last_committee = CommitteeProfile.objects.order_by('-id').first()
            if last_committee and last_committee.committee_id:
                try:
                    last_num = int(last_committee.committee_id.split('-')[-1])
                    new_num = last_num + 1
                except:
                    new_num = random.randint(1000, 9999)
            else:
                new_num = 1000
            return f"COM-{year}-{new_num:04d}"

        # Set role and create profiles
        if role == 'superuser':
            user.is_superuser = True
            user.is_staff = True
            user.save()

        elif role == 'staff':
            user.is_staff = True
            user.save()
            group, _ = Group.objects.get_or_create(name='Staff')
            user.groups.add(group)
            StaffProfile.objects.get_or_create(
                user=user,
                defaults={
                    'staff_id': generate_staff_id(),
                    'position': request.POST.get('position', 'Loan Officer'),
                    'is_active': True
                }
            )

        elif role == 'cashier':
            user.is_staff = True
            user.save()
            group, _ = Group.objects.get_or_create(name='Cashier')
            user.groups.add(group)
            CashierProfile.objects.get_or_create(
                user=user,
                defaults={
                    'cashier_id': generate_cashier_id(),
                    'is_active': True
                }
            )

        elif role == 'manager':
            user.is_staff = True
            user.save()
            group, _ = Group.objects.get_or_create(name='Manager')
            user.groups.add(group)
            ManagerProfile.objects.get_or_create(
                user=user,
                defaults={
                    'manager_id': generate_manager_id(),
                    'is_active': True
                }
            )

        elif role == 'committee':
            user.is_staff = True
            user.save()
            group, _ = Group.objects.get_or_create(name='Committee')
            user.groups.add(group)
            CommitteeProfile.objects.get_or_create(
                user=user,
                defaults={
                    'committee_id': generate_committee_id(),
                    'is_active': True
                }
            )

        elif role == 'regular_member':
            # Create Regular Member (non-employee)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            Member.objects.create(
                user=user,
                membership_number=generate_membership_number(),
                first_name=first_name or username,
                last_name=last_name or '',
                contact_number=request.POST.get('contact_number', ''),
                residence_address=request.POST.get('address', ''),
                monthly_income=Decimal(request.POST.get('monthly_income', 0)),
                employment_status='member',
                salary_loan_eligible=False,
                is_active=is_active,
                verification_status='verified',
                account_status='active'
            )

        elif role == 'employee_member':
            # Create Employee Member (has salary loan access)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            Member.objects.create(
                user=user,
                membership_number=generate_membership_number(),
                first_name=first_name or username,
                last_name=last_name or '',
                contact_number=request.POST.get('contact_number', ''),
                residence_address=request.POST.get('address', ''),
                monthly_income=Decimal(request.POST.get('monthly_income', 0)),
                position=request.POST.get('position', ''),
                employee_id=generate_employee_id(),  # ✅ SYSTEM GENERATED
                employment_status='employee',
                salary_loan_eligible=True,
                is_active=is_active,
                verification_status='verified',
                account_status='active'
            )
        else:
            # Normal user (no member profile)
            user.is_staff = False
            user.is_superuser = False
            user.save()

        _log_audit(request.user, 'create', 'User', user.id, request=request)
        return JsonResponse({'success': True, 'message': f'User {username} created'})

    return JsonResponse({'error': 'Invalid method'}, status=405)


@super_admin_required
def user_delete(request, user_id):
    """Delete a user"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            if user.id == request.user.id:
                return JsonResponse({'success': False, 'error': 'You cannot delete your own account'})
            username = user.username
            user.delete()
            _log_audit(request.user, 'delete', 'User', user_id, request=request)
            return JsonResponse({'success': True, 'message': f'User {username} deleted'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'User not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ==================== MEMBERS MANAGEMENT ====================

@super_admin_required
def members_list(request):
    members = Member.objects.all().order_by('-created_at')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', 'all')

    if search:
        members = members.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(membership_number__icontains=search) |
            Q(contact_number__icontains=search)
        )

    if status == 'active':
        members = members.filter(is_active=True)
    elif status == 'inactive':
        members = members.filter(is_active=False)

    active_count = Member.objects.filter(is_active=True).count()
    inactive_count = Member.objects.filter(is_active=False).count()
    total_income = Member.objects.aggregate(total=Sum('monthly_income'))['total'] or 0

    return render(request, 'admin_panel/members_list.html', {
        'members': members,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_income': total_income,
    })


@super_admin_required
def member_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        middle_initial = request.POST.get('middle_initial', '')
        contact_number = request.POST.get('contact_number', '')
        residence_address = request.POST.get('residence_address', '')
        monthly_income = Decimal(request.POST.get('monthly_income', 0))

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('admin_panel:members_list')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        while True:
            membership_number = f"M-{random.randint(10000, 99999)}"
            if not Member.objects.filter(membership_number=membership_number).exists():
                break

        member = Member.objects.create(
            user=user,
            membership_number=membership_number,
            first_name=first_name,
            last_name=last_name,
            middle_initial=middle_initial,
            contact_number=contact_number,
            residence_address=residence_address,
            monthly_income=monthly_income,
            is_active=True
        )

        messages.success(request, f'Member {first_name} {last_name} created')
        return redirect('admin_panel:members_list')

    return render(request, 'admin_panel/member_form.html', {'action': 'Create'})


@super_admin_required
def member_detail(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    return JsonResponse({
        "id": member.id,
        "membership_number": member.membership_number,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "middle_initial": member.middle_initial or "",
        "email": member.user.email if member.user else "",
        "contact_number": member.contact_number or "",
        "residence_address": member.residence_address or "",
        "monthly_income": str(member.monthly_income),
        "is_active": member.is_active,
    })


@super_admin_required
def member_edit(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        member.first_name = request.POST.get('first_name', member.first_name)
        member.last_name = request.POST.get('last_name', member.last_name)
        member.middle_initial = request.POST.get('middle_initial', member.middle_initial)
        member.contact_number = request.POST.get('contact_number', member.contact_number)
        member.residence_address = request.POST.get('residence_address', member.residence_address)
        member.monthly_income = Decimal(request.POST.get('monthly_income', member.monthly_income))
        member.is_active = request.POST.get('is_active') == 'on'
        member.save()

        user = member.user
        user.first_name = member.first_name
        user.last_name = member.last_name
        user.email = request.POST.get('email', user.email)
        user.save()

        messages.success(request, f'Member updated successfully')
        return redirect('admin_panel:members_list')

    return render(request, 'admin_panel/member_form.html', {'member': member, 'action': 'Edit'})


@super_admin_required
def member_delete(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        name = f"{member.first_name} {member.last_name}"
        member.delete()
        messages.success(request, f'Member {name} deleted')
        return redirect('admin_panel:members_list')
    return render(request, 'admin_panel/member_confirm_delete.html', {'member': member})


# ==================== LOAN PRODUCTS MANAGEMENT ====================

@super_admin_required
def loan_products_list(request):
    products = LoanProduct.objects.all().order_by('name')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', 'all')

    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(display_name__icontains=search)
        )

    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)

    active_count = LoanProduct.objects.filter(is_active=True).count()
    inactive_count = LoanProduct.objects.filter(is_active=False).count()
    avg_interest = LoanProduct.objects.aggregate(avg=Avg('interest_rate'))['avg'] or 0

    return render(request, 'admin_panel/loan_products_list.html', {
        'products': products,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'avg_interest': round(avg_interest, 1),
    })


@super_admin_required
def loan_product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        display_name = request.POST.get('display_name')
        interest_rate = Decimal(request.POST.get('interest_rate', 0))
        term_months = int(request.POST.get('term_months', 12))
        min_amount = Decimal(request.POST.get('min_amount', 0))
        max_amount = Decimal(request.POST.get('max_amount', 0))
        is_active = request.POST.get('is_active') == 'on'

        product = LoanProduct.objects.create(
            name=name.upper(),
            display_name=display_name,
            interest_rate=interest_rate,
            term_months=term_months,
            term_days=term_months * 30,
            min_amount=min_amount,
            max_amount=max_amount,
            is_active=is_active
        )
        messages.success(request, f'Product {product.name} created')
        return redirect('admin_panel:loan_products_list')

    return render(request, 'admin_panel/loan_product_form.html', {'action': 'Create'})


@super_admin_required
def loan_product_detail(request, product_id):
    product = get_object_or_404(LoanProduct, id=product_id)
    return JsonResponse({
        "id": product.id,
        "name": product.name,
        "display_name": product.display_name,
        "description": getattr(product, "description", ""),
        "interest_rate": str(product.interest_rate),
        "term_months": product.term_months,
        "term_days": getattr(product, "term_days", product.term_months * 30),
        "min_amount": str(product.min_amount),
        "max_amount": str(product.max_amount),
        "is_active": product.is_active,
        "created_at": product.created_at.strftime("%Y-%m-%d %H:%M") if product.created_at else None,
    })


@super_admin_required
def loan_product_edit(request, product_id):
    product = get_object_or_404(LoanProduct, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.display_name = request.POST.get('display_name')
        product.interest_rate = Decimal(request.POST.get('interest_rate', 0))
        product.term_months = int(request.POST.get('term_months', 12))
        product.min_amount = Decimal(request.POST.get('min_amount', 0))
        product.max_amount = Decimal(request.POST.get('max_amount', 0))
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()
        messages.success(request, 'Product updated')
        return redirect('admin_panel:loan_products_list')
    return render(request, 'admin_panel/loan_product_form.html', {'product': product, 'action': 'Edit'})


@super_admin_required
def loan_product_delete(request, product_id):
    product = get_object_or_404(LoanProduct, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product {name} deleted')
        return redirect('admin_panel:loan_products_list')
    return render(request, 'admin_panel/loan_product_confirm_delete.html', {'product': product})


# ==================== LOAN APPLICATIONS ====================

@super_admin_required
def loan_applications_list(request):
    applications = LoanApplication.objects.all().order_by('-applied_date')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', 'all')

    if search:
        applications = applications.filter(
            Q(application_id__icontains=search) |
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search)
        )

    if status and status != 'all':
        applications = applications.filter(status=status)

    total_applications = LoanApplication.objects.count()
    pending_count = LoanApplication.objects.filter(status='pending_staff_review').count()
    approved_count = LoanApplication.objects.filter(status__in=['line_approved', 'manager_approved']).count()
    rejected_count = LoanApplication.objects.filter(status='rejected').count()

    return render(request, 'admin_panel/loan_applications_list.html', {
        'applications': applications,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@super_admin_required
def loan_application_detail(request, app_id):
    app = get_object_or_404(LoanApplication, id=app_id)
    return JsonResponse({
        "id": app.id,
        "application_id": app.application_id,
        "member_name": f"{app.member.first_name} {app.member.last_name}",
        "requested_amount": str(app.requested_amount),
        "status": app.status,
        "loan_product": app.loan_product.name if app.loan_product else "-",
        "purpose": app.purpose or "-",
        "date_applied": app.created_at.strftime("%Y-%m-%d %H:%M"),
    })


@super_admin_required
def loan_application_create(request):
    if request.method == 'POST':
        try:
            member_id = request.POST.get('member_id')
            product_id = request.POST.get('product_id')
            amount = Decimal(request.POST.get('amount', 0))
            purpose = request.POST.get('purpose', '')
            collateral = request.POST.get('collateral', '')

            member = get_object_or_404(Member, id=member_id)
            product = get_object_or_404(LoanProduct, id=product_id) if product_id else None

            app_id = f"APP-{datetime.now().year}-{random.randint(1000, 9999)}"

            application = LoanApplication.objects.create(
                application_id=app_id,
                member=member,
                loan_product=product,
                requested_amount=amount,
                purpose=purpose,
                collateral_offered=collateral,
                status='pending_staff_review',
                applicant_user=member.user
            )
            messages.success(request, f'Application {app_id} created successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:loan_applications_list')

    members = Member.objects.filter(is_active=True)
    products = LoanProduct.objects.filter(is_active=True)
    return render(request, 'admin_panel/loan_application_form.html', {
        'members': members,
        'products': products,
        'action': 'Create'
    })


@super_admin_required
def loan_application_edit(request, app_id):
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        app.requested_amount = Decimal(request.POST.get('amount', 0))
        app.purpose = request.POST.get('purpose', '')
        app.collateral_offered = request.POST.get('collateral', '')
        app.status = request.POST.get('status', app.status)
        app.save()
        messages.success(request, f'Application updated')
        return redirect('admin_panel:loan_applications_list')

    members = Member.objects.filter(is_active=True)
    products = LoanProduct.objects.filter(is_active=True)
    return render(request, 'admin_panel/loan_application_form.html', {
        'app': app,
        'members': members,
        'products': products,
        'action': 'Edit'
    })


@super_admin_required
def loan_application_delete(request, app_id):
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        app.delete()
        messages.success(request, 'Application deleted')
        return redirect('admin_panel:loan_applications_list')
    return render(request, 'admin_panel/loan_application_confirm_delete.html', {'app': app})


# ==================== LOANS ====================

@super_admin_required
def loans_list(request):
    loans = Loan.objects.all().order_by('-created_at')

    total_loans = Loan.objects.count()
    active_count = Loan.objects.filter(status='active').count()
    completed_count = Loan.objects.filter(status='paid').count()
    total_amount = Loan.objects.aggregate(total=Sum('amount'))['total'] or 0  # ← FIXED!

    return render(request, 'admin_panel/loans_list.html', {
        'loans': loans,
        'total_loans': total_loans,
        'active_count': active_count,
        'completed_count': completed_count,
        'total_amount': total_amount,
    })


@super_admin_required
def loan_detail(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    return JsonResponse({
        "id": loan.id,
        "loan_number": loan.loan_number,
        "borrower_name": f"{loan.borrower.first_name} {loan.borrower.last_name}",
        "principal_amount": str(loan.amount),  # ← FIXED!
        "remaining_balance": str(loan.remaining_balance),
        "interest_rate": str(loan.interest_rate),
        "term_months": loan.term_months,
        "status": loan.status,
        "disbursement_date": loan.disbursement_date.strftime("%Y-%m-%d") if loan.disbursement_date else None,
        "due_date": loan.due_date.strftime("%Y-%m-%d") if loan.due_date else None,
    })


@super_admin_required
def loan_create(request):
    if request.method == 'POST':
        try:
            borrower_id = request.POST.get('borrower_id')
            product_id = request.POST.get('product_id')
            principal_amount = Decimal(request.POST.get('principal_amount', 0))
            interest_rate = Decimal(request.POST.get('interest_rate', 0))
            term_months = int(request.POST.get('term_months', 12))

            borrower = get_object_or_404(Member, id=borrower_id)
            product = get_object_or_404(LoanProduct, id=product_id)

            year = timezone.now().year
            last_loan = Loan.objects.filter(loan_number__startswith=f'LN-{year}').order_by('-id').first()
            if last_loan:
                last_num = int(last_loan.loan_number.split('-')[-1])
                loan_number = f'LN-{year}-{str(last_num + 1).zfill(4)}'
            else:
                loan_number = f'LN-{year}-1000'

            loan = Loan.objects.create(
                loan_number=loan_number,
                borrower=borrower,
                loan_product=product,
                principal_amount=principal_amount,
                remaining_balance=principal_amount,
                interest_rate=interest_rate,
                term_months=term_months,
                term_days=term_months * 30,
                disbursement_date=timezone.now().date(),
                due_date=timezone.now().date() + timedelta(days=term_months * 30),
                status='active'
            )
            messages.success(request, f'Loan {loan_number} created')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:loans_list')

    return redirect('admin_panel:loans_list')


@super_admin_required
def loan_edit(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        try:
            loan.status = request.POST.get('status', loan.status)
            loan.save()
            messages.success(request, f'Loan {loan.loan_number} updated')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:loans_list')
    return redirect('admin_panel:loans_list')


# ==================== PAYMENT SCHEDULES ====================

@super_admin_required
def payment_schedules_list(request):
    schedules = PaymentSchedule.objects.all().order_by('due_date')

    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')

    if search:
        schedules = schedules.filter(
            Q(loan__loan_number__icontains=search) |
            Q(loan__borrower__first_name__icontains=search) |
            Q(loan__borrower__last_name__icontains=search)
        )

    if status and status != 'all':
        schedules = schedules.filter(status=status)

    active_loans = Loan.objects.filter(status='active')

    total_schedules = PaymentSchedule.objects.count()
    paid_count = PaymentSchedule.objects.filter(status='paid').count()
    pending_count = PaymentSchedule.objects.filter(status='pending').count()

    return render(request, 'admin_panel/payment_schedules_list.html', {
        'schedules': schedules,
        'active_loans': active_loans,
        'total_schedules': total_schedules,
        'paid_count': paid_count,
        'pending_count': pending_count,
    })


@super_admin_required
def payment_schedule_generate(request):
    if request.method == 'POST':
        try:
            loan_id = request.POST.get('loan_id')
            loan = get_object_or_404(Loan, id=loan_id)

            # Delete existing schedules
            PaymentSchedule.objects.filter(loan=loan).delete()

            principal = loan.amount
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

                PaymentSchedule.objects.create(
                    loan=loan,
                    schedule_number=month,
                    due_date=due_date,
                    principal_due=principal_due,
                    interest_due=interest_due,
                    penalty_due=0,
                    total_due=monthly_payment,
                    status='pending'
                )
                remaining_balance -= principal_due

            messages.success(request, f'Payment schedule generated for loan {loan.loan_number}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:payment_schedules_list')

    return redirect('admin_panel:payment_schedules_list')


@super_admin_required
def payment_schedule_detail(request, schedule_id):
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    return JsonResponse({
        'id': schedule.id,
        'loan_number': schedule.loan.loan_number,
        'borrower_name': f"{schedule.loan.borrower.first_name} {schedule.loan.borrower.last_name}",
        'due_date': schedule.due_date.strftime('%Y-%m-%d'),
        'principal_due': str(schedule.principal_due),
        'interest_due': str(schedule.interest_due),
        'total_due': str(schedule.total_due),
        'status': schedule.status,
    })


@super_admin_required
def payment_schedule_edit(request, schedule_id):
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    if request.method == 'POST':
        try:
            schedule.due_date = request.POST.get('due_date')
            schedule.principal_due = Decimal(request.POST.get('principal_due', 0))
            schedule.interest_due = Decimal(request.POST.get('interest_due', 0))
            schedule.total_due = schedule.principal_due + schedule.interest_due
            schedule.status = request.POST.get('status', schedule.status)
            schedule.save()
            messages.success(request, 'Schedule updated')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:payment_schedules_list')

    return redirect('admin_panel:payment_schedules_list')


@super_admin_required
def payment_schedule_mark_paid(request, schedule_id):
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    if request.method == 'POST':
        schedule.status = 'paid'
        schedule.paid_date = timezone.now().date()
        schedule.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@super_admin_required
def payment_schedule_delete(request, schedule_id):
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    if request.method == 'POST':
        schedule.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# ==================== PAYMENTS ====================

@super_admin_required
def payments_list(request):
    payments = Payment.objects.all().order_by('-payment_date')

    search = request.GET.get('search', '').strip()
    method = request.GET.get('method', '')

    if search:
        payments = payments.filter(
            Q(payment_number__icontains=search) |
            Q(loan__loan_number__icontains=search) |
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search)
        )

    if method and method != 'all':
        payments = payments.filter(payment_method=method)

    active_loans = Loan.objects.filter(status='active')
    total_payments = Payment.objects.count()
    total_amount = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'admin_panel/payments_list.html', {
        'payments': payments,
        'active_loans': active_loans,
        'total_payments': total_payments,
        'total_amount': total_amount,
    })


@super_admin_required
def payment_create(request):
    if request.method == 'POST':
        try:
            loan_id = request.POST.get('loan_id')
            amount = Decimal(request.POST.get('amount', 0))
            payment_date = request.POST.get('payment_date', timezone.now().date())
            payment_method = request.POST.get('payment_method', 'cash')
            reference_number = request.POST.get('reference_number', '')

            loan = get_object_or_404(Loan, id=loan_id)

            year = timezone.now().year
            last_payment = Payment.objects.filter(payment_number__startswith=f'PAY-{year}').order_by('-id').first()
            if last_payment:
                last_num = int(last_payment.payment_number.split('-')[-1])
                payment_number = f'PAY-{year}-{str(last_num + 1).zfill(6)}'
            else:
                payment_number = f'PAY-{year}-000001'

            payment = Payment.objects.create(
                payment_number=payment_number,
                loan=loan,
                member=loan.borrower,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
                reference_number=reference_number if payment_method != 'cash' else '',
                status='completed'
            )

            loan.remaining_balance -= amount
            if loan.remaining_balance <= 0:
                loan.status = 'paid'
                loan.remaining_balance = 0
            loan.save()

            messages.success(request, f'Payment {payment_number} recorded successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:payments_list')

    return redirect('admin_panel:payments_list')


@super_admin_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return JsonResponse({
        'id': payment.id,
        'payment_number': payment.payment_number,
        'loan_number': payment.loan.loan_number if payment.loan else '-',
        'borrower_name': f"{payment.member.first_name} {payment.member.last_name}" if payment.member else '-',
        'amount': str(payment.amount),
        'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
        'payment_method': payment.payment_method,
        'reference_number': payment.reference_number,
        'status': payment.status,
    })


@super_admin_required
def payment_edit(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        try:
            old_amount = payment.amount
            new_amount = Decimal(request.POST.get('amount', payment.amount))
            payment.amount = new_amount
            payment.payment_date = request.POST.get('payment_date', payment.payment_date)
            payment.payment_method = request.POST.get('payment_method', payment.payment_method)
            payment.reference_number = request.POST.get('reference_number', '')
            payment.save()

            if payment.loan:
                amount_diff = new_amount - old_amount
                payment.loan.remaining_balance -= amount_diff
                if payment.loan.remaining_balance <= 0:
                    payment.loan.status = 'paid'
                    payment.loan.remaining_balance = 0
                payment.loan.save()

            messages.success(request, f'Payment updated successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:payments_list')

    return redirect('admin_panel:payments_list')


@super_admin_required
def payment_receipt(request, payment_id):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from io import BytesIO

    payment = get_object_or_404(Payment, id=payment_id)
    loan = payment.loan
    borrower = loan.borrower

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16,
                                 textColor=colors.HexColor('#1e3c72'), alignment=TA_CENTER)

    story = []
    story.append(Paragraph("TOMPuCO COOPERATIVE", title_style))
    story.append(Paragraph("OFFICIAL PAYMENT RECEIPT", styles['Normal']))
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"Receipt Number: {payment.payment_number}", styles['Normal']))
    story.append(Paragraph(f"Date: {payment.payment_date.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Paragraph(f"Member: {borrower.first_name} {borrower.last_name}", styles['Normal']))
    story.append(Paragraph(f"Loan Number: {loan.loan_number}", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Amount Paid: ₱{payment.amount:,.2f}", styles['Normal']))
    story.append(Paragraph(f"Payment Method: {payment.get_payment_method_display()}", styles['Normal']))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Thank you for your payment!", styles['Normal']))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{payment.payment_number}.pdf"'
    return response


@super_admin_required
def payment_delete(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment_number = payment.payment_number
        payment.delete()
        return JsonResponse({'success': True, 'message': f'Payment {payment_number} deleted'})
    return JsonResponse({'success': False})


# ==================== PAYMENT RECEIPTS ====================

@super_admin_required
def payment_receipts_list(request):
    receipts = PaymentReceipt.objects.all().order_by('-generated_at')
    return render(request, 'admin_panel/payment_receipts_list.html', {
        'receipts': receipts,
        'total_receipts': receipts.count(),
    })


# ==================== MEMBER DOCUMENTS ====================

@super_admin_required
def member_documents_list(request):
    documents = MemberDocument.objects.all().order_by('-uploaded_at')

    total_documents = MemberDocument.objects.count()
    verified_count = MemberDocument.objects.filter(is_verified=True).count()
    pending_count = MemberDocument.objects.filter(is_verified=False).count()

    return render(request, 'admin_panel/member_documents_list.html', {
        'documents': documents,
        'total_documents': total_documents,
        'verified_count': verified_count,
        'pending_count': pending_count,
    })


@super_admin_required
def member_document_create(request):
    if request.method == 'POST':
        try:
            member_id = request.POST.get('member_id')
            document_type = request.POST.get('document_type')
            document_number = request.POST.get('document_number', '')
            document_file = request.FILES.get('document_file')

            member = get_object_or_404(Member, id=member_id)

            MemberDocument.objects.create(
                member=member,
                document_type=document_type,
                document_number=document_number,
                file=document_file,
                is_verified=False
            )
            messages.success(request, f'Document uploaded for {member.first_name}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:member_documents_list')

    return redirect('admin_panel:member_documents_list')


@super_admin_required
def member_document_verify(request, doc_id):
    """Verify a member document"""
    if request.method == 'POST':
        try:
            doc = MemberDocument.objects.get(id=doc_id)
            doc.is_verified = True
            doc.save()
            _log_audit(request.user, 'update', 'MemberDocument', doc_id, request=request)
            return JsonResponse({'success': True, 'message': 'Document verified successfully'})
        except MemberDocument.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Document not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@super_admin_required
def member_document_delete(request, doc_id):
    """Delete a member document"""
    if request.method == 'POST':
        try:
            doc = MemberDocument.objects.get(id=doc_id)
            doc.delete()
            _log_audit(request.user, 'delete', 'MemberDocument', doc_id, request=request)
            return JsonResponse({'success': True, 'message': 'Document deleted successfully'})
        except MemberDocument.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Document not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# ==================== LOAN ATTACHMENTS ====================

@super_admin_required
def loan_attachments_list(request):
    attachments = LoanAttachment.objects.all().order_by('-attached_at')

    all_applications = LoanApplication.objects.all().order_by('-applied_date')  # ← FIXED!
    all_documents = MemberDocument.objects.all()

    return render(request, 'admin_panel/loan_attachments_list.html', {
        'attachments': attachments,
        'all_applications': all_applications,
        'all_documents': all_documents,
        'total_attachments': attachments.count(),
    })

@super_admin_required
def loan_attachment_create(request):
    if request.method == 'POST':
        try:
            application_id = request.POST.get('application_id')
            document_id = request.POST.get('document_id')
            is_reused = request.POST.get('is_reused') == 'on'

            loan_app = get_object_or_404(LoanApplication, id=application_id)
            document = get_object_or_404(MemberDocument, id=document_id)

            attachment = LoanAttachment.objects.create(
                loan_application=loan_app,
                document=document,
                is_reused=is_reused
            )
            messages.success(request, f'Attachment added to application {loan_app.application_id}')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('admin_panel:loan_attachments_list')

    return redirect('admin_panel:loan_attachments_list')


@super_admin_required
def loan_attachment_detail(request, att_id):
    att = get_object_or_404(LoanAttachment, id=att_id)
    return JsonResponse({
        'id': att.id,
        'application_id': att.loan_application.application_id,
        'member_name': f"{att.loan_application.member.first_name} {att.loan_application.member.last_name}",
        'document_type': att.document.get_document_type_display() if hasattr(att.document,
                                                                             'get_document_type_display') else att.document.document_type,
        'document_number': att.document.document_number,
        'is_reused': att.is_reused,
        'attached_at': att.attached_at.strftime('%Y-%m-%d %H:%M'),
        'file_url': att.document.file.url if att.document.file else None,
    })


@super_admin_required
def loan_attachment_delete(request, att_id):
    if request.method == 'POST':
        att = get_object_or_404(LoanAttachment, id=att_id)
        att.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# ==================== COMMITTEE DECISIONS ====================

@super_admin_required
def committee_decisions_list(request):
    decisions = CommitteeDecision.objects.all().order_by('-voted_at')
    return render(request, 'admin_panel/committee_decisions_list.html', {
        'decisions': decisions,
        'total_decisions': decisions.count(),
    })


# ==================== NOTIFICATIONS ====================

@super_admin_required
def notifications_list(request):
    notifications = Notification.objects.all().order_by('-created_at')

    total_notifications = Notification.objects.count()
    read_count = Notification.objects.filter(is_read=True).count()
    unread_count = Notification.objects.filter(is_read=False).count()

    return render(request, 'admin_panel/notifications_list.html', {
        'notifications': notifications,
        'total_notifications': total_notifications,
        'read_count': read_count,
        'unread_count': unread_count,
    })


@super_admin_required
def notification_mark_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@super_admin_required
def notification_delete(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id)
    if request.method == 'POST':
        notification.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def notifications_api(request):
    """API endpoint for admin notifications"""
    from main.models import Notification

    notifications = Notification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:20]

    unread_count = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    data = {
        'success': True,
        'unread_count': unread_count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message[:100],
            'link': n.link,
            'notification_type': n.notification_type,
            'created_at': n.created_at.isoformat(),
            'is_read': n.is_read,
        } for n in notifications]
    }
    return JsonResponse(data)


@login_required
def mark_notification_read_api(request, notif_id):
    """Mark notification as read"""
    from main.models import Notification

    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@login_required
def mark_all_notifications_read_api(request):
    """Mark all notifications as read"""
    from main.models import Notification

    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse(
            {'success': True, 'count': Notification.objects.filter(recipient=request.user, is_read=False).count()})
    return JsonResponse({'success': False})


# ==================== AUDIT LOGS ====================

@super_admin_required
def audit_logs_list(request):
    logs = AuditLog.objects.all().order_by('-created_at')

    total_logs = AuditLog.objects.count()
    create_count = AuditLog.objects.filter(action='create').count()
    update_count = AuditLog.objects.filter(action='update').count()
    delete_count = AuditLog.objects.filter(action='delete').count()

    return render(request, 'admin_panel/audit_logs_list.html', {
        'logs': logs,
        'total_logs': total_logs,
        'create_count': create_count,
        'update_count': update_count,
        'delete_count': delete_count,
    })


@super_admin_required
def audit_log_detail(request, log_id):
    log = get_object_or_404(AuditLog, id=log_id)
    return JsonResponse({
        'id': log.id,
        'user': log.user.username if log.user else 'System',
        'action': log.action,
        'entity_type': log.entity_type,
        'entity_id': log.entity_id,
        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


# ==================== SYSTEM SETTINGS ====================

@super_admin_required
def system_settings_list(request):
    settings = SystemSetting.objects.all().order_by('setting_key')
    return render(request, 'admin_panel/system_settings_list.html', {'settings': settings})


@super_admin_required
def system_setting_update(request, setting_id):
    setting = get_object_or_404(SystemSetting, id=setting_id)
    if request.method == 'POST':
        setting.setting_value = request.POST.get('value', setting.setting_value)
        setting.updated_by = request.user
        setting.save()
        return JsonResponse({'success': True, 'value': setting.setting_value})
    return JsonResponse({'success': False})


# ==================== REPORTS ====================

@super_admin_required
def reports(request):
    total_members = Member.objects.count()
    total_loans = Loan.objects.count()
    total_disbursed = Loan.objects.aggregate(total=Sum('amount'))['total'] or 0  # ← FIXED!
    total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    collection_rate = (total_payments / total_disbursed * 100) if total_disbursed > 0 else 0

    return render(request, 'admin_panel/reports.html', {
        'total_members': total_members,
        'total_loans': total_loans,
        'total_disbursed': total_disbursed,
        'collection_rate': round(collection_rate, 1),
    })


def reports_api(request, report_type):
    if report_type == 'member_report':
        members = Member.objects.all()
        data = {'success': True, 'title': 'Member Report',
                'headers': ['ID', 'Membership #', 'Name', 'Contact', 'Join Date', 'Status'], 'rows': []}
        for m in members:
            data['rows'].append(
                [m.id, m.membership_number or '-', f"{m.first_name} {m.last_name}", m.contact_number or '-',
                 m.created_at.strftime('%Y-%m-%d') if m.created_at else '-', 'Active' if m.is_active else 'Inactive'])
        return JsonResponse(data)

    elif report_type == 'loan_report':
        loans = Loan.objects.all()
        data = {'success': True, 'title': 'Loan Summary Report',
                'headers': ['Loan #', 'Member', 'Principal', 'Balance', 'Status'], 'rows': []}
        for l in loans:
            data['rows'].append(
                [l.loan_number, f"{l.borrower.first_name} {l.borrower.last_name}" if l.borrower else '-',
                 f"₱{l.amount:,.2f}", f"₱{l.remaining_balance:,.2f}", l.status])  # ← FIXED: l.principal_amount -> l.amount
        return JsonResponse(data)

    else:
        data = {'success': True, 'title': 'Report', 'headers': ['Category', 'Value'],
                'rows': [['Sample Data', 'Working']]}
        return JsonResponse(data)

#member verify

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def verify_member(request, member_id):
    """Admin view to verify or reject member registration"""
    member = get_object_or_404(Member, id=member_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'verify':
            member.verification_status = 'verified'
            member.verification_date = timezone.now()
            member.verified_by = request.user
            member.max_loan_amount = Decimal('50000')  # Increase limit
            member.max_active_loans = 1
            member.is_active = True
            member.member_tier = 'standard'

            # Send notification to member
            Notification.objects.create(
                user=member.user,
                title="Account Verified!",
                message="Your account has been verified. You can now apply for loans.",
                notification_type='system'
            )

            messages.success(request, f"Member {member.user.username} has been verified.")

        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '')
            member.verification_status = 'rejected'
            member.rejection_reason = rejection_reason
            member.is_active = False

            # Send notification to member
            Notification.objects.create(
                user=member.user,
                title="Account Verification Failed",
                message=f"Your account verification was rejected. Reason: {rejection_reason}",
                notification_type='alert'
            )

            messages.warning(request, f"Member {member.user.username} has been rejected.")

        elif action == 'suspend':
            suspension_reason = request.POST.get('suspension_reason', '')
            member.verification_status = 'suspended'
            member.is_restricted = True
            member.restriction_reason = suspension_reason
            member.restricted_until = request.POST.get('restricted_until') or None
            member.is_active = False

            messages.warning(request, f"Member {member.user.username} has been suspended.")

        member.save()
        return redirect('admin_panel:members_list')

    context = {
        'member': member,
        'today': date.today(),
    }
    return render(request, 'admin_panel/verify_member.html', context)


@login_required
@super_admin_required
def verify_member_ajax(request, member_id):
    """Verify a pending member via AJAX"""
    if request.method == 'POST':
        try:
            member = Member.objects.get(id=member_id)
            member.verification_status = 'verified'
            member.account_status = 'active'
            member.is_active = True
            member.save()

            # Also activate the user
            user = member.user
            user.is_active = True
            user.save()

            # Send notification
            from main.notification_helper import create_notification
            create_notification(
                recipient=user,
                notification_type='system',
                title='Account Verified!',
                message=f'Congratulations {member.first_name}! Your account has been verified. You can now apply for loans.',
                link='/dashboard/'
            )

            return JsonResponse({'success': True})
        except Member.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Member not found'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})