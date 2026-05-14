# main/views.py - COMPLETE CORRECTED VERSION

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, authenticate, login as auth_login
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.urls import reverse_lazy
from .forms import CustomLoginForm
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta, date
import random
import json
import base64
import csv
import secrets
import io
from io import StringIO, BytesIO

# QR Code
import qrcode

from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# Django OTP
from django_otp.plugins.otp_totp.models import TOTPDevice

# Main models (only what exists in main/models.py)
from .models import (
    Member, Loan, LoanApplication, LoanProduct,
    Payment, PaymentSchedule, Notification, MemberDocument,
    CommitteeDecision, AuditLog, SystemSetting, PaymentReceipt,
    PaymentReminder, CommitteeVote, generate_membership_number, generate_employee_id
)

# Import from other apps
from staff.models import StaffProfile
from committee.models import CommitteeProfile
from cashier.models import CashierProfile
from manager.models import ManagerProfile

# Forms and helpers
from main.forms import MemberRegistrationForm
from main.notification_helper import create_notification, get_user_notifications, get_unread_count

# OTP storage
otp_storage = {}

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required


@login_required
def role_based_redirect(request):
    """Redirect users to their appropriate dashboard based on role"""
    user = request.user

    # Check for different user types and redirect accordingly
    if hasattr(user, 'cashier_profile'):
        return redirect('cashier:dashboard')
    elif hasattr(user, 'staff_profile'):
        return redirect('staff:dashboard')
    if hasattr(user, 'committee_profile'):
        return redirect('committee:dashboard')
    elif hasattr(user, 'manager_profile'):
        return redirect('manager:dashboard')
    elif user.is_superuser:
        return redirect('admin_panel:dashboard')
    elif hasattr(user, 'member_profile'):
        return redirect('main:dashboard')
    else:
        # Default fallback
        return redirect('main:dashboard')


# ============================================================
# QR CODE GENERATION FUNCTIONS
# ============================================================

def generate_member_qr_code(member):
    """Generate QR code for member"""
    qr_data = member.membership_number
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d6e6e", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


def generate_loan_qr_code(loan):
    """Generate QR code for loan payment"""
    qr_data = loan.loan_number
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d6e6e", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()


# ============================================================
# AUTHENTICATION VIEWS
# ============================================================

def staff_login(request):
    """Custom login view that redirects to staff dashboard"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'staff_profile') or request.user.is_staff:
            return redirect('staff:dashboard')
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            if user.is_staff or hasattr(user, 'staff_profile'):
                return redirect('staff:dashboard')
            else:
                messages.warning(request, 'You do not have staff access.')
                return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'main/staff_login.html')


class CustomLoginView(LoginView):
    template_name = 'main/login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user = request.user

            # Superuser redirect
            if user.is_superuser:
                return redirect('admin_panel:dashboard')

            # Staff/Loan Officer redirect
            if hasattr(user, 'staff_profile'):
                return redirect('staff:dashboard')

            # Cashier redirect
            if hasattr(user, 'cashier_profile'):
                return redirect('cashier:dashboard')

            # Committee redirect
            if hasattr(user, 'committee_profile'):
                return redirect('committee:dashboard')

            # Manager redirect
            if hasattr(user, 'manager_profile'):
                return redirect('manager:dashboard')

            # Group redirects (fallback if profiles don't exist)
            if user.groups.filter(name='Manager').exists():
                return redirect('manager:dashboard')
            if user.groups.filter(name='Committee').exists():
                return redirect('committee:dashboard')
            if user.groups.filter(name='Cashier').exists():
                return redirect('cashier:dashboard')

            # Check for staff flag
            if user.is_staff:
                return redirect('staff:dashboard')

            # Regular member
            if hasattr(user, 'member_profile'):
                return redirect('main:dashboard')

            # Default fallback
            return redirect('main:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user

        # Superuser redirect
        if user.is_superuser:
            return reverse_lazy('admin_panel:dashboard')

        # Staff/Loan Officer redirect
        if hasattr(user, 'staff_profile'):
            return reverse_lazy('staff:dashboard')

        # Cashier redirect
        if hasattr(user, 'cashier_profile'):
            return reverse_lazy('cashier:dashboard')

        # Committee redirect
        if hasattr(user, 'committee_profile'):
            return reverse_lazy('committee:dashboard')

        # Manager redirect
        if hasattr(user, 'manager_profile'):
            return reverse_lazy('manager:dashboard')

        # Group redirects (fallback)
        if user.groups.filter(name='Manager').exists():
            return reverse_lazy('manager:dashboard')
        if user.groups.filter(name='Committee').exists():
            return reverse_lazy('committee:dashboard')
        if user.groups.filter(name='Cashier').exists():
            return reverse_lazy('cashier:dashboard')

        # Staff flag
        if user.is_staff:
            return reverse_lazy('staff:dashboard')

        # Regular member
        if hasattr(user, 'member_profile'):
            return reverse_lazy('main:dashboard')

        # Default fallback
        return reverse_lazy('main:dashboard')


def landing_page(request):
    return render(request, 'main/landing.html')


def custom_logout(request):
    logout(request)
    return redirect('/')


from django.http import HttpResponse
from django.contrib.auth import get_user_model


def create_admin(request):
    User = get_user_model()
    username = 'admin'
    password = 'Admin123!'
    email = 'admin@tompuco.com'

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        return HttpResponse(f"""
        <h2>✅ Admin User Created Successfully!</h2>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>Password:</strong> {password}</p>
        <p><a href="/login/">Click here to login</a></p>
        <hr>
        <p style="color: red;"><strong>Important:</strong> Remove this view after logging in!</p>
        """)
    else:
        return HttpResponse(f"""
        <h2>⚠️ Admin User Already Exists</h2>
        <p><strong>Username:</strong> {username}</p>
        <p><strong>Password:</strong> {password}</p>
        <p><a href="/login/">Click here to login</a></p>
        """)


def check_username(request):
    """API endpoint to check if username exists"""
    username = request.GET.get('username', '')
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'exists': exists})


def check_email(request):
    """API endpoint to check if email exists"""
    email = request.GET.get('email', '')
    exists = User.objects.filter(email__iexact=email).exists()
    return JsonResponse({'exists': exists})


def verification_pending(request):
    """Verification pending page"""
    # If user is already verified, redirect to dashboard
    if request.user.is_authenticated and hasattr(request.user, 'member_profile'):
        member = request.user.member_profile
        if member.verification_status == 'verified' and member.is_active:
            return redirect('main:dashboard')
    return render(request, 'main/verification_pending.html')


def register(request):
    if request.method == 'POST':
        from datetime import datetime

        # Helper function for safe Decimal conversion
        def safe_decimal(value, default=0):
            if value and str(value).strip() and str(value) != '':
                try:
                    return Decimal(str(value))
                except:
                    return Decimal(str(default))
            return Decimal(str(default))

        def safe_int(value, default=0):
            if value and str(value).strip():
                try:
                    return int(value)
                except:
                    return default
            return default

        # Get basic account data
        username = request.POST.get('username')
        password = request.POST.get('password1')
        email = request.POST.get('email')
        user_type = request.POST.get('user_type')

        # Get personal data
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        middle_initial = request.POST.get('middle_initial', '')
        nickname = request.POST.get('nickname', '')
        civil_status = request.POST.get('civil_status', 'single')
        nationality = request.POST.get('nationality', 'Filipino')

        # Convert birthdate
        birthdate_str = request.POST.get('birthdate')
        if birthdate_str and birthdate_str.strip():
            try:
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except:
                birthdate = None
        else:
            birthdate = None

        gender = request.POST.get('gender')
        contact_number = request.POST.get('contact_number')
        residence_address = request.POST.get('residence_address')
        spouse_name = request.POST.get('spouse_name', '')
        num_dependents = safe_int(request.POST.get('num_dependents', 0))

        # Farm data
        farm_location = request.POST.get('farm_location', '')
        farm_owned_hectares = safe_decimal(request.POST.get('farm_owned_hectares', 0))
        farm_leased_hectares = safe_decimal(request.POST.get('farm_leased_hectares', 0))
        area_planted = safe_decimal(request.POST.get('area_planted', 0))
        new_plant = safe_decimal(request.POST.get('new_plant', 0))
        ratoon_crops = safe_decimal(request.POST.get('ratoon_crops', 0))
        adjacent_farm = request.POST.get('adjacent_farm', '')

        # Income data
        monthly_income = safe_decimal(request.POST.get('monthly_income', 0))

        # Employee specific fields
        employee_position = request.POST.get('position', '')
        employee_id = request.POST.get('employee_id', '')
        date_hired_str = request.POST.get('date_hired', '')

        if date_hired_str and date_hired_str.strip() and user_type == 'employee':
            try:
                date_hired = datetime.strptime(date_hired_str, '%Y-%m-%d').date()
            except:
                date_hired = None
        else:
            date_hired = None

        # Validate
        if user_type not in ['member', 'employee']:
            messages.error(request, "Invalid account type selected.")
            return render(request, 'registration/register.html')

        if not all([username, password, email, last_name, first_name, contact_number, residence_address]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'registration/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'registration/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'registration/register.html')

        try:
            # Create User
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )

            # Generate UNIQUE membership number with retry logic
            import random
            max_attempts = 10
            membership_number = None

            for attempt in range(max_attempts):
                # Generate number like M-37897 (based on your pattern)
                new_number = random.randint(10000, 99999)
                test_number = f"M-{new_number}"

                # Also check M-2026-XXXX format
                test_number2 = f"M-{datetime.now().year}-{new_number:04d}"

                if not Member.objects.filter(membership_number=test_number).exists() and \
                        not Member.objects.filter(membership_number=test_number2).exists():
                    membership_number = test_number
                    break

            # If all attempts failed, use timestamp
            if not membership_number:
                membership_number = f"M-{int(datetime.now().timestamp())}"

            # Create Member profile
            member = Member.objects.create(
                user=user,
                membership_number=membership_number,
                first_name=first_name,
                last_name=last_name,
                middle_initial=middle_initial if middle_initial else None,
                nickname=nickname if nickname else None,
                civil_status=civil_status,
                birthdate=birthdate,
                gender=gender if gender else None,
                nationality=nationality,
                contact_number=contact_number,
                residence_address=residence_address,
                spouse_name=spouse_name if spouse_name else None,
                num_dependents=num_dependents,
                farm_location=farm_location if farm_location else None,
                farm_owned_hectares=farm_owned_hectares,
                farm_leased_hectares=farm_leased_hectares,
                area_planted=area_planted,
                new_plant=new_plant,
                ratoon_crops=ratoon_crops,
                adjacent_farm=adjacent_farm if adjacent_farm else None,
                monthly_income=monthly_income,
                employment_status=user_type,
                employee_id=employee_id if user_type == 'employee' else None,
                position=employee_position if user_type == 'employee' else None,
                date_hired=date_hired,
                salary_loan_eligible=(user_type == 'employee'),
                max_regular_loan=Decimal('10000'),
                max_salary_loan=Decimal('50000') if user_type == 'employee' else Decimal('0'),
                max_active_loans=0,
                verification_status='pending',
                account_status='pending',
                member_tier='basic',
                is_active=False,
            )

            # Notify admins
            from main.notification_helper import create_notification
            for admin in User.objects.filter(is_superuser=True):
                create_notification(
                    recipient=admin,
                    notification_type='system',
                    title='New Member Registration',
                    message=f'{first_name} {last_name} registered as {user_type}. Awaiting verification.',
                    link='/superadmin/members/'
                )

            # Notify staff
            from staff.models import StaffProfile
            for staff_profile in StaffProfile.objects.filter(is_active=True):
                create_notification(
                    recipient=staff_profile.user,
                    notification_type='system',
                    title='New Member Registration',
                    message=f'{first_name} {last_name} registered. Pending verification.',
                    link='/staff/members/'
                )

            # Send confirmation to member
            create_notification(
                recipient=user,
                notification_type='system',
                title='Registration Received',
                message=f'Thank you for registering {first_name}! Your account is pending verification.',
                link='/verification-pending/'  # ← CHANGE THIS
            )

            messages.success(request,
                             f"Registration submitted! Your membership number is {membership_number}. Your account will be verified within 24-48 hours.")
            return redirect('main:verification_pending')

        except IntegrityError as e:
            # Clean up user if member creation failed
            if User.objects.filter(username=username).exists():
                User.objects.filter(username=username).delete()
            messages.error(request, f"Registration failed: {str(e)}")
            return render(request, 'registration/register.html')
        except Exception as e:
            if User.objects.filter(username=username).exists():
                User.objects.filter(username=username).delete()
            import traceback
            traceback.print_exc()
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'registration/register.html')

    return render(request, 'registration/register.html')


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_profile_completeness(member):
    required_fields = [
        member.first_name, member.last_name, member.contact_number,
        member.residence_address, member.birthdate, member.gender,
        member.monthly_income
    ]
    filled = sum(1 for field in required_fields if field)
    total = len(required_fields)
    return int((filled / total) * 100) if total > 0 else 0


def log_audit(user, action, entity_type, entity_id=None, old_values=None, new_values=None, request=None):
    audit_log = AuditLog(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else '',
        old_values=old_values,
        new_values=new_values
    )
    if request:
        audit_log.ip_address = request.META.get('REMOTE_ADDR')
        audit_log.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    audit_log.save()


# ============================================================
# MEMBER DASHBOARD VIEWS
# ============================================================

@login_required
def dashboard(request):
    user = request.user

    # Superuser redirect
    if user.is_superuser:
        return redirect('admin_panel:dashboard')

    # Staff/Loan Officer redirect
    if hasattr(user, 'staff_profile'):
        return redirect('staff:dashboard')

    # Cashier redirect
    if hasattr(user, 'cashier_profile'):
        return redirect('cashier:dashboard')

    # Committee redirect
    if hasattr(user, 'committee_profile'):
        return redirect('committee:dashboard')

    # Manager redirect
    if hasattr(user, 'manager_profile'):
        return redirect('manager:dashboard')

    # Group redirects (fallback)
    if user.groups.filter(name='Manager').exists():
        return redirect('manager:dashboard')
    if user.groups.filter(name='Committee').exists():
        return redirect('committee:dashboard')
    if user.groups.filter(name='Cashier').exists():
        return redirect('cashier:dashboard')

    # Staff flag
    if user.is_staff:
        return redirect('staff:dashboard')

    # Regular member dashboard
    try:
        member = user.member_profile
        # FIXED: changed 'borrower' to 'member'
        loans = Loan.objects.filter(member=member)
        # FIXED: changed 'principal_amount' to 'amount'
        total_loaned = loans.aggregate(total=Sum('amount'))['total'] or Decimal(0)
        active_loans = loans.filter(status='active')
        total_paid = Payment.objects.filter(member=member, status='completed').aggregate(total=Sum('amount'))['total'] or Decimal(0)
        # FIXED: changed '-created_at' to '-applied_date' if needed
        applications = LoanApplication.objects.filter(member=member).order_by('-applied_date')[:5]
        pending_applications = LoanApplication.objects.filter(member=member, status='pending_staff_review').count()
        profile_completeness = calculate_profile_completeness(member)
        unread_count = get_unread_count(user)

        total_remaining = active_loans.aggregate(total=Sum('remaining_balance'))['total'] or Decimal(0)

        next_due = None
        for loan in active_loans:
            if loan.due_date:
                if not next_due or loan.due_date < next_due:
                    next_due = loan.due_date

        qr_image = generate_member_qr_code(member)

        context = {
            'member': member,
            'total_loaned': total_loaned,
            'active_loans_count': active_loans.count(),
            'active_loans': active_loans[:3],
            'total_paid': total_paid,
            'total_remaining_balance': total_remaining,
            'next_due_date': next_due,
            'recent_applications': applications,
            'pending_applications': pending_applications,
            'profile_completeness': profile_completeness,
            'unread_notifications_count': unread_count,
            'qr_image': qr_image,
        }
        return render(request, 'main/dashboard.html', context)

    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your member profile.')
        return redirect('main:edit_profile')


@login_required
def member_profile(request):
    try:
        member = request.user.member_profile
        profile_completeness = calculate_profile_completeness(member)
        documents_count = MemberDocument.objects.filter(member=member).count()
        # FIXED: changed 'borrower' to 'member'
        total_loans = Loan.objects.filter(member=member).count()
        # FIXED: changed 'principal_amount' to 'amount'
        total_borrowed = Loan.objects.filter(member=member, status='paid').aggregate(
            total=Sum('amount'))['total'] or Decimal(0)
        comaker_loans = 0  # Set to 0 if co_maker field doesn't exist
        qr_image = generate_member_qr_code(member)

        return render(request, 'main/member_profile.html', {
            'member': member,
            'profile_completeness': profile_completeness,
            'documents_count': documents_count,
            'total_loans': total_loans,
            'total_borrowed': total_borrowed,
            'comaker_loans': comaker_loans,
            'qr_image': qr_image,
        })
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your profile first.')
        return redirect('main:edit_profile')


@login_required
def member_qr_code(request):
    try:
        member = request.user.member_profile
        qr_image = generate_member_qr_code(member)

        context = {
            'member': member,
            'qr_image': qr_image,
            'qr_data': member.membership_number,
        }
        return render(request, 'main/member_qr.html', context)
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your profile first.')
        return redirect('main:edit_profile')


@login_required
def edit_profile(request):
    member = request.user.member_profile

    if request.method == 'POST':
        try:
            from datetime import datetime

            def clean_string(value, max_length=None):
                if value is None or value == 'None' or value == 'null' or value == '':
                    return ''
                value = str(value).strip()
                if max_length and len(value) > max_length:
                    value = value[:max_length]
                return value

            # Basic Info
            first_name = clean_string(request.POST.get('first_name', ''))
            last_name = clean_string(request.POST.get('last_name', ''))
            middle_initial = clean_string(request.POST.get('middle_initial', ''), max_length=1)
            nickname = clean_string(request.POST.get('nickname', ''))
            nationality = request.POST.get('nationality', 'Filipino')
            if nationality == 'None':
                nationality = 'Filipino'

            # Gender
            gender = request.POST.get('gender', '')
            if gender == 'None':
                gender = ''

            # Age
            age = request.POST.get('age', 0)
            if age == 'None' or age == '':
                age = 0
            else:
                try:
                    age = int(age)
                except:
                    age = 0

            # Contact and Address
            contact_number = clean_string(request.POST.get('contact_number', ''))
            residence_address = clean_string(request.POST.get('residence_address', ''))
            spouse_name = clean_string(request.POST.get('spouse_name', ''))

            # Dependents
            num_dependents = request.POST.get('num_dependents', 0)
            if num_dependents == 'None' or num_dependents == '':
                num_dependents = 0
            else:
                try:
                    num_dependents = int(num_dependents)
                except:
                    num_dependents = 0

            # Farm Location
            farm_location = clean_string(request.POST.get('farm_location', ''))

            # ============================================
            # BIRTHDATE FIX - DON'T PARSE IF ALREADY DATE
            # ============================================
            birthdate_input = request.POST.get('birthdate')
            # Only update birthdate if a new value was provided AND it's not the existing date object
            if birthdate_input and birthdate_input != 'None' and birthdate_input != '':
                # Check if it's a string (from form input)
                if isinstance(birthdate_input, str):
                    try:
                        # Try YYYY-MM-DD format
                        member.birthdate = datetime.strptime(birthdate_input, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            # Try DD/MM/YYYY format
                            member.birthdate = datetime.strptime(birthdate_input, '%d/%m/%Y').date()
                        except ValueError:
                            # Invalid date format, keep existing
                            pass
            # If no birthdate provided, keep existing (don't change)

            # ============================================
            # PROFILE PICTURE
            # ============================================
            if request.FILES.get('profile_picture'):
                if member.profile_picture:
                    try:
                        member.profile_picture.delete(save=False)
                    except:
                        pass
                member.profile_picture = request.FILES['profile_picture']

            if request.POST.get('remove_profile_picture') == 'on':
                if member.profile_picture:
                    try:
                        member.profile_picture.delete(save=False)
                    except:
                        pass
                    member.profile_picture = None

            # ============================================
            # SAVE USER
            # ============================================
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # ============================================
            # SAVE MEMBER
            # ============================================
            member.first_name = first_name
            member.last_name = last_name
            member.middle_initial = middle_initial
            member.nickname = nickname
            member.nationality = nationality
            member.gender = gender
            member.age = age
            member.contact_number = contact_number
            member.residence_address = residence_address
            member.spouse_name = spouse_name
            member.num_dependents = num_dependents
            member.farm_location = farm_location
            member.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('main:member_profile')

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('main:edit_profile')

    return render(request, 'main/edit_profile.html', {'member': member})


@login_required
def upload_valid_id(request):
    if request.method == 'POST' and request.FILES.get('valid_id'):
        try:
            member = request.user.member_profile
            file = request.FILES['valid_id']
            member.uploaded_id = file
            member.save()
            MemberDocument.objects.create(
                member=member,
                document_type='valid_id',
                file=file,
                is_verified=False
            )
            log_audit(request.user, 'update', 'Member', member.id, request=request)
            return JsonResponse({'success': True, 'message': 'ID uploaded successfully'})
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Member profile not found'}, status=404)
    return JsonResponse({'error': 'No file uploaded'}, status=400)


@login_required
def upload_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            member = request.user.member_profile
            if member.profile_picture:
                try:
                    member.profile_picture.delete(save=False)
                except:
                    pass
            member.profile_picture = request.FILES['avatar']
            member.save()
            messages.success(request, 'Profile picture updated successfully!')
        except Exception as e:
            messages.error(request, f'Error uploading image: {str(e)}')
    else:
        messages.error(request, 'No image selected')

    return redirect('main:member_profile')


# ============================================================
# LOAN APPLICATION VIEWS
# ============================================================

@login_required
def apply_loan(request):
    try:
        member = request.user.member_profile
        loan_products = LoanProduct.objects.filter(is_active=True)

        # Check if member is employee
        is_employee = member.employment_status == 'employee'  # ✅ FIXED

        context = {
            'member': member,
            'loan_products': loan_products,
            'is_employee': is_employee,  # Pass this to template
            'has_active_loan': Loan.objects.filter(member=member, status='active').exists(),
        }
        return render(request, 'main/apply_loan.html', context)
    except Member.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('main:edit_profile')


@login_required
def submit_loan_application(request):
    if request.method == 'POST':
        try:
            import json
            from datetime import date
            import random

            data = json.loads(request.body)

            # Get member
            if not hasattr(request.user, 'member_profile'):
                return JsonResponse({'success': False, 'error': 'Member profile not found'})

            member = request.user.member_profile

            # Get loan product
            loan_type = data.get('loan_type')
            try:
                loan_product = LoanProduct.objects.get(name=loan_type)
            except LoanProduct.DoesNotExist:
                return JsonResponse({'success': False, 'error': f'Loan product {loan_type} not found'})

            # Create application with correct field names
            application = LoanApplication.objects.create(
                application_id=f"APP-{loan_product.name}-{date.today().year}-{random.randint(1000, 9999)}",
                member=member,
                loan_product=loan_product,
                amount=data.get('amount'),
                purpose=data.get('purpose'),
                status='pending_staff_review',
                applied_date=date.today()
            )

            return JsonResponse({'success': True, 'application_id': application.id})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})


@login_required
def search_co_maker(request):
    if request.method == 'GET':
        member_id = request.GET.get('member_id')
        try:
            co_maker = Member.objects.get(membership_number=member_id)
            if co_maker.id == request.user.member_profile.id:
                return JsonResponse({'error': 'You cannot be your own co-maker'}, status=400)
            if not co_maker.is_active:
                return JsonResponse({'error': 'Co-maker account is inactive'}, status=400)

            active_loans_as_comaker = Loan.objects.filter(member=co_maker, status='active').count()
            is_eligible = active_loans_as_comaker < 3

            return JsonResponse({
                'success': True,
                'id': co_maker.id,
                'name': f"{co_maker.last_name}, {co_maker.first_name}",
                'contact': co_maker.contact_number,
                'address': co_maker.residence_address,
                'membership': co_maker.membership_number,
                'is_eligible': is_eligible,
                'active_loans_as_comaker': active_loans_as_comaker
            })
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Member not found.'}, status=404)


@login_required
def validate_co_maker(request, co_maker_id):
    try:
        co_maker = get_object_or_404(Member, id=co_maker_id)
        active_loans_as_comaker = Loan.objects.filter(member=co_maker, status='active').count()
        is_eligible = active_loans_as_comaker < 3

        return JsonResponse({
            'valid': is_eligible,
            'active_loans': active_loans_as_comaker,
            'max_allowed': 3,
            'message': f'This co-maker has {active_loans_as_comaker} active loan(s). Maximum allowed is 3.' if not is_eligible else 'Co-maker is eligible and valid!'
        })
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Co-maker not found'}, status=404)


# ============================================================
# OTP VIEWS
# ============================================================

@login_required
def send_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        phone = data.get('phone')
        otp = str(random.randint(100000, 999999))
        otp_storage[request.user.id] = {
            'otp': otp,
            'expires': timezone.now() + timedelta(minutes=5),
            'attempts': 0
        }
        print(f"[OTP] To {phone}: {otp}")
        request.session['demo_otp'] = otp
        return JsonResponse({'success': True, 'message': 'OTP sent successfully.'})


@login_required
def verify_otp(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_otp = data.get('otp')
        stored = otp_storage.get(request.user.id)

        if stored:
            if stored['attempts'] >= 3:
                return JsonResponse({'success': False, 'error': 'Too many failed attempts.'})
            if stored['expires'] < timezone.now():
                return JsonResponse({'success': False, 'error': 'OTP expired.'})
            if stored['otp'] == user_otp:
                request.session['otp_verified'] = True
                return JsonResponse({'success': True, 'message': 'OTP verified!'})
            else:
                stored['attempts'] += 1
                remaining = 3 - stored['attempts']
                return JsonResponse({'success': False, 'error': f'Invalid OTP. {remaining} attempts left.'})

        return JsonResponse({'success': False, 'error': 'No OTP request found.'})


# ============================================================
# SIGNATURE VIEWS
# ============================================================

@login_required
def save_signature(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            signature_data = data.get('signature')
            member = request.user.member_profile
            member.signature = signature_data
            member.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


# ============================================================
# LOAN AND APPLICATION VIEWS
# ============================================================

@login_required
def my_applications(request):
    try:
        applications = LoanApplication.objects.filter(member=request.user.member_profile).order_by('-applied_date')
        status_colors = {
            'pending_staff_review': 'warning',
            'with_committee': 'info',
            'line_approved': 'primary',
            'pending_manager_approval': 'warning',
            'manager_approved': 'success',
            'active': 'success',
            'rejected': 'danger',
            'needs_revision': 'danger',
            'ready_for_disbursement': 'info',
            'disbursed': 'success',
        }
        for app in applications:
            app.status_color = status_colors.get(app.status, 'secondary')
        return render(request, 'main/my_applications.html', {'applications': applications})
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


@login_required
def my_loans(request):
    try:
        # FIXED: changed 'borrower' to 'member'
        loans = Loan.objects.filter(member=request.user.member_profile).order_by('-created_at')
        status_colors = {
            'pending_disbursement': 'warning',
            'active': 'success',
            'overdue': 'danger',
            'restructured': 'info',
            'paid': 'secondary',
            'defaulted': 'danger',
        }
        for loan in loans:
            loan.total_paid = Payment.objects.filter(loan=loan, status='completed').aggregate(total=Sum('amount'))[
                                  'total'] or Decimal(0)
            loan.status_color = status_colors.get(loan.status, 'secondary')
            loan.payment_percentage = int(
                (loan.total_paid / loan.total_payable) * 100) if loan.total_payable > 0 else 0
            next_schedule = PaymentSchedule.objects.filter(loan=loan, status='pending').order_by('due_date').first()
            loan.next_payment_due = next_schedule.due_date if next_schedule else None
            loan.next_payment_amount = next_schedule.total_due if next_schedule else None
        return render(request, 'main/my_loans.html', {'loans': loans})
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


@login_required
def payment_history(request):
    try:
        payments = Payment.objects.filter(member=request.user.member_profile).order_by('-payment_date')
        total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal(0)
        paginator = Paginator(payments, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        return render(request, 'main/payment_history.html', {'payments': page_obj, 'total_paid': total_paid})
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


@login_required
def view_application_details(request, app_id):
    try:
        application = get_object_or_404(LoanApplication, id=app_id, member=request.user.member_profile)
        committee_decisions = CommitteeDecision.objects.filter(loan_application=application)

        status_steps = [
            {'key': 'pending_staff_review', 'label': 'Submitted', 'icon': '📋', 'completed': True},
            {'key': 'with_committee', 'label': 'Committee Review', 'icon': '👥',
             'completed': application.status in ['with_committee', 'line_approved', 'pending_manager_approval',
                                                 'manager_approved', 'active', 'ready_for_disbursement', 'disbursed']},
            {'key': 'line_approved', 'label': 'Line Approved', 'icon': '✓',
             'completed': application.status in ['line_approved', 'pending_manager_approval', 'manager_approved',
                                                 'active', 'ready_for_disbursement', 'disbursed']},
            {'key': 'pending_manager_approval', 'label': 'Manager Approval', 'icon': '👔',
             'completed': application.status in ['manager_approved', 'active', 'ready_for_disbursement', 'disbursed']},
            {'key': 'manager_approved', 'label': 'Approved', 'icon': '✅',
             'completed': application.status in ['manager_approved', 'active', 'ready_for_disbursement', 'disbursed']},
            {'key': 'ready_for_disbursement', 'label': 'Ready for Release', 'icon': '💰',
             'completed': application.status in ['ready_for_disbursement', 'disbursed']},
            {'key': 'disbursed', 'label': 'Loan Released', 'icon': '🏦', 'completed': application.status == 'disbursed'},
        ]

        current_step_index = -1
        for i, step in enumerate(status_steps):
            if step['key'] == application.status:
                current_step_index = i
                break

        context = {
            'application': application,
            'committee_decisions': committee_decisions,
            'status_steps': status_steps,
            'current_step_index': current_step_index,
        }
        return render(request, 'main/view_application.html', context)
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


@login_required
def payment_schedule(request, loan_id):
    try:
        # FIXED: changed 'borrower' to 'member'
        loan = get_object_or_404(Loan, id=loan_id, member=request.user.member_profile)
        schedules = PaymentSchedule.objects.filter(loan=loan).order_by('due_date')

        total_principal = schedules.aggregate(total=Sum('principal_due'))['total'] or Decimal(0)
        total_interest = schedules.aggregate(total=Sum('interest_due'))['total'] or Decimal(0)
        total_penalty = schedules.aggregate(total=Sum('penalty_due'))['total'] or Decimal(0)
        total_due = schedules.aggregate(total=Sum('total_due'))['total'] or Decimal(0)
        paid_principal = schedules.filter(status='paid').aggregate(total=Sum('principal_due'))['total'] or Decimal(0)
        paid_interest = schedules.filter(status='paid').aggregate(total=Sum('interest_due'))['total'] or Decimal(0)

        context = {
            'loan': loan,
            'schedules': schedules,
            'next_payment': schedules.filter(status='pending').first(),
            'paid_count': schedules.filter(status='paid').count(),
            'pending_count': schedules.filter(status='pending').count(),
            'total_principal': total_principal,
            'total_interest': total_interest,
            'total_penalty': total_penalty,
            'total_due': total_due,
            'paid_principal': paid_principal,
            'paid_interest': paid_interest,
        }
        return render(request, 'main/payment_schedule.html', context)
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


# ============================================================
# RECEIPT DOWNLOAD VIEW
# ============================================================

@login_required
def download_receipt(request, payment_id):
    try:
        payment = get_object_or_404(Payment, id=payment_id, member=request.user.member_profile)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{payment.payment_number}.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 24)
        p.drawString(180, height - 50, "TOMPuCO COOPERATIVE")
        p.setFont("Helvetica-Bold", 16)
        p.drawString(220, height - 80, "OFFICIAL RECEIPT")

        p.setFont("Helvetica", 11)
        y = height - 120
        p.drawString(50, y, f"Receipt Number: {payment.payment_number}")
        p.drawString(50, y - 20, f"Date: {payment.payment_date.strftime('%B %d, %Y')}")
        p.drawString(50, y - 40, f"Time: {payment.created_at.strftime('%I:%M %p')}")
        p.drawString(50, y - 60, f"Member: {payment.member.last_name}, {payment.member.first_name}")
        p.drawString(50, y - 80, f"Membership #: {payment.member.membership_number}")
        p.drawString(50, y - 100, f"Loan Number: {payment.loan.loan_number}")

        p.line(50, y - 115, width - 50, y - 115)

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y - 140, "PAYMENT DETAILS")
        p.setFont("Helvetica", 11)
        p.drawString(50, y - 160, f"Amount Paid: ₱{payment.amount:,.2f}")
        p.drawString(50, y - 180, f"Payment Method: {payment.get_payment_method_display()}")

        if payment.reference_number:
            p.drawString(50, y - 200, f"Reference #: {payment.reference_number}")

        p.drawString(50, y - 230, "Breakdown:")
        p.drawString(70, y - 250, f"Principal: ₱{payment.principal_amount:,.2f}")
        p.drawString(70, y - 270, f"Interest: ₱{payment.interest_amount:,.2f}")
        if payment.penalty_amount > 0:
            p.drawString(70, y - 290, f"Penalty: ₱{payment.penalty_amount:,.2f}")

        p.line(50, y - 310, width - 50, y - 310)
        p.drawString(50, y - 330, f"Remaining Balance: ₱{payment.remaining_balance_after:,.2f}")

        p.setFont("Helvetica-Oblique", 10)
        p.drawString(180, 50, "Thank you for your payment!")
        p.drawString(160, 35, "This is a system-generated receipt.")

        p.save()
        return response
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


# ============================================================
# COLLATERAL UPLOAD VIEW
# ============================================================

@login_required
def upload_collateral(request, application_id):
    if request.method == 'POST' and request.FILES.get('collateral_doc'):
        try:
            application = get_object_or_404(LoanApplication, id=application_id, member=request.user.member_profile)

            collateral_file = request.FILES['collateral_doc']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"collateral_{application.application_id}_{timestamp}.{collateral_file.name.split('.')[-1]}"

            saved_path = default_storage.save(f'collateral/{file_name}', collateral_file)
            application.collateral_offered = f"Document uploaded: {file_name}"
            application.save()

            MemberDocument.objects.create(
                member=application.member,
                document_type='collateral',
                document_number=application.application_id,
                file=saved_path,
                is_verified=False
            )

            log_audit(request.user, 'update', 'LoanApplication', application.id, request=request)

            return JsonResponse({'success': True, 'message': 'Collateral document uploaded successfully'})
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Member profile not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'No file uploaded'}, status=400)


# ============================================================
# NOTIFICATION VIEWS
# ============================================================

@login_required
def get_notifications_api(request):
    notifications = get_user_notifications(request.user, 30)
    unread_count = get_unread_count(request.user)
    data = {
        'unread_count': unread_count,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'type': n.notification_type,
            'created_at': n.created_at.strftime('%Y-%m-%d %I:%M %p'),
            'is_read': n.is_read
        } for n in notifications]
    }
    return JsonResponse(data)


@login_required
def mark_notification_read(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


# ============================================================
# LOAN STATUS API
# ============================================================

@login_required
def member_loan_status(request):
    try:
        member = request.user.member_profile
        # FIXED: changed 'borrower' to 'member'
        active_loans = Loan.objects.filter(member=member, status='active')
        has_active_loan = active_loans.exists()
        outstanding_balance = active_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0

        return JsonResponse({
            'has_active_loan': has_active_loan,
            'outstanding_balance': float(outstanding_balance),
            'active_loan_count': active_loans.count(),
        })
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Member profile not found'}, status=404)


# ============================================================
# DOCUMENT MANAGEMENT VIEWS
# ============================================================

@login_required
def my_documents(request):
    try:
        member = request.user.member_profile
        documents = MemberDocument.objects.filter(member=member).order_by('-uploaded_at')
        return render(request, 'main/my_documents.html', {'member': member, 'documents': documents})
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


@login_required
def upload_document(request):
    if request.method == 'POST':
        try:
            member = request.user.member_profile
            document_type = request.POST.get('document_type')
            file = request.FILES.get('file')

            if not file:
                return JsonResponse({'error': 'No file provided'}, status=400)

            doc = MemberDocument.objects.create(
                member=member,
                document_type=document_type,
                file=file,
                is_verified=False
            )
            log_audit(request.user, 'create', 'MemberDocument', doc.id, request=request)
            return JsonResponse({'success': True, 'message': 'Document uploaded successfully', 'document_id': doc.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def delete_document(request, doc_id):
    if request.method == 'POST':
        try:
            member = request.user.member_profile
            document = get_object_or_404(MemberDocument, id=doc_id, member=member)
            document.delete()
            log_audit(request.user, 'delete', 'MemberDocument', doc_id, request=request)
            return JsonResponse({'success': True, 'message': 'Document deleted successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)


# ============================================================
# CHATBOT VIEW
# ============================================================

@login_required
def chatbot_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('message', '').lower().strip()

            # Simple response logic
            if 'hello' in question or 'hi' in question or 'hey' in question:
                response = "👋 Hello! Welcome to ToMPuCo Assistant. How can I help you today?"
            elif 'apply' in question or 'application' in question:
                response = """📝 **How to Apply for a Loan:**

1️⃣ Click "Apply for Loan" on your dashboard
2️⃣ Select loan type and amount
3️⃣ Add co-maker (if required)
4️⃣ Upload required documents
5️⃣ Draw your signature and verify OTP

Staff will review your application within 24-48 hours."""
            elif 'balance' in question or 'remaining' in question:
                response = """💰 **Check Your Balance:**

Go to "My Loans" page on your dashboard.
Click on your active loan to see:
• Principal amount
• Remaining balance
• Next payment due date
• Monthly payment amount"""
            elif 'pay' in question or 'payment' in question:
                response = """💳 **How to Pay Your Loan:**

1️⃣ Visit our office
2️⃣ Go to STAFF first - they will issue Payment Instruction Slip
3️⃣ Take the slip to CASHIER to pay

Accepted Methods: Cash, Pesada (Scale Ticket), Quedan (Sugar QS)"""
            elif 'requirement' in question or 'need' in question or 'document' in question:
                response = """📋 **Loan Requirements:**

✅ Valid ID (Government-issued)
✅ Proof of Income (Payslip/Business permit)
✅ Collateral Documents (Land Title, etc.)
✅ Co-maker (required for most loans)

💡 Salary Loan does NOT require a co-maker."""
            elif 'interest' in question or 'rate' in question:
                response = """📊 **Interest Rates:**

• NCL: 20% per annum
• APCP: 15% per annum
• Salary Loan: 8% per annum
• Collateralized: 20% per annum
• Providential: 16% per annum

💡 Interest is diminishing - decreases each month as you pay."""
            elif 'co-maker' in question or 'comaker' in question:
                response = """👥 **About Co-maker:**

✅ Must be an active ToMPuCo member
✅ No overdue loans
✅ Cannot be yourself
✅ Maximum 3 active loans as co-maker

💡 Salary Loan does NOT require a co-maker."""
            elif 'status' in question:
                response = """📌 **Application Status Meanings:**

• Pending Staff Review - Staff is reviewing
• With Committee - With committee for approval
• Line Approved - Committee approved amount
• Pending Manager Approval - Waiting for manager
• Active - Loan disbursed
• Rejected - Denied (reason provided)

Go to "My Applications" page to see exact status."""
            elif 'contact' in question or 'support' in question or 'call' in question:
                response = """📞 **Contact Us:**

📱 Phone: (035) 123-4567
📧 Email: support@tompuco.com.ph
📍 Address: Villareal, Bayawan City, Negros Oriental

🕐 Office Hours:
Monday - Friday: 7:00 AM - 4:00 PM
Saturday: 8:00 AM - 12:00 PM
Sunday: Closed"""
            elif 'qr' in question or 'scan' in question or 'code' in question:
                response = """📱 **QR Code Payment:**

You can find your QR code in:
• Your Profile page
• Dashboard "My QR Code" section

Show this QR code to the cashier for faster payment processing!"""
            elif 'thank' in question or 'salamat' in question:
                response = "🙏 You're welcome! Is there anything else I can help you with?"
            else:
                response = """🤖 **I'm ToMPuCo Assistant!**

I can help you with:
• How to apply for a loan
• Check your balance
• Payment methods
• Loan requirements
• Interest rates
• Co-maker information
• Application status
• QR Code payment
• Contact information

Just type your question above or click one of the quick reply buttons!"""

            return JsonResponse({'response': response})

        except Exception as e:
            print(f"Chatbot error: {e}")
            return JsonResponse({'response': 'Sorry, an error occurred. Please try again.'})

    return JsonResponse({'error': 'POST request required'}, status=405)


# ============================================================
# EXPORT VIEWS
# ============================================================

@login_required
def export_payment_history_csv(request):
    try:
        member = request.user.member_profile
        payments = Payment.objects.filter(member=member, status='completed').order_by('-payment_date')

        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="payment_history_{datetime.now().strftime("%Y%m%d")}.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['Payment Date', 'Receipt Number', 'Loan Number', 'Amount', 'Method', 'Principal', 'Interest', 'Penalty',
             'Remaining Balance'])

        for payment in payments:
            writer.writerow([
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.payment_number,
                payment.loan.loan_number,
                f"{payment.amount:,.2f}",
                payment.get_payment_method_display(),
                f"{payment.principal_amount:,.2f}",
                f"{payment.interest_amount:,.2f}",
                f"{payment.penalty_amount:,.2f}",
                f"{payment.remaining_balance_after:,.2f}"
            ])

        return response
    except Member.DoesNotExist:
        messages.error(request, 'Member profile not found.')
        return redirect('main:edit_profile')


# ============================================================
# LOAN CALCULATOR VIEW
# ============================================================

@login_required
def loan_calculator(request):
    try:
        member = request.user.member_profile

        if request.method == 'POST':
            amount = Decimal(request.POST.get('amount', 0))
            term = int(request.POST.get('term', 12))
            interest_rate = Decimal(request.POST.get('interest_rate', 20))

            monthly_rate = (interest_rate / 100) / 12

            if monthly_rate > 0:
                monthly_payment = (amount * monthly_rate * (1 + monthly_rate) ** term) / (
                        (1 + monthly_rate) ** term - 1)
            else:
                monthly_payment = amount / term

            total_payable = monthly_payment * term
            total_interest = total_payable - amount

            service_charge = amount * Decimal('0.02')
            cbu_retention = amount * Decimal('0.01')
            insurance_charge = amount * Decimal('0.005')
            total_deductions = service_charge + cbu_retention + insurance_charge + Decimal('35') + Decimal('200')
            net_proceeds = amount - total_deductions

            return JsonResponse({
                'monthly_payment': float(monthly_payment),
                'total_interest': float(total_interest),
                'total_payable': float(total_payable),
                'service_charge': float(service_charge),
                'net_proceeds': float(net_proceeds),
                'total_deductions': float(total_deductions)
            })

        return render(request, 'main/loan_calculator.html', {'member': member})
    except Member.DoesNotExist:
        return redirect('main:edit_profile')


# ============================================================
# CHANGE PASSWORD VIEW
# ============================================================

@login_required
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully. Please login again.')
            return redirect('main:login')

    return render(request, 'main/change_password.html')


# ============================================================
# LOAN TYPES VIEW
# ============================================================

@login_required
def loan_types(request):
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        member = None

    context = {
        'member': member,
    }
    return render(request, 'main/loan_types.html', context)


# ============================================================
# API VIEWS FOR MEMBER DATA - FIXED
# ============================================================

@login_required
def member_applications_api(request):
    """API endpoint for member's loan applications"""
    try:
        # Check if user has member profile
        if not hasattr(request.user, 'member_profile'):
            return JsonResponse({
                'success': False,
                'error': 'Member profile not found',
                'applications': []
            }, status=200)

        member = request.user.member_profile

        # Get applications ordered by most recent first (using applied_date, not created_at)
        applications = LoanApplication.objects.filter(member=member).order_by('-applied_date')

        # Build response data
        applications_data = []
        for app in applications:
            applications_data.append({
                'id': app.id,
                'application_id': app.application_id,
                'loan_type': app.loan_product.display_name if app.loan_product else 'APCP',
                'amount': float(app.amount) if app.amount else 0,
                'approved_line': float(app.approved_line) if app.approved_line else None,
                'status': app.status,
                'status_display': app.get_status_display() if hasattr(app,
                                                                      'get_status_display') else app.status.replace('_',
                                                                                                                    ' ').title(),
                'applied_date': app.applied_date.strftime('%Y-%m-%d') if app.applied_date else '',
                'purpose': app.purpose or '',
                'collateral_offered': app.collateral_offered or '',
                'mode_of_payment': app.mode_of_payment or 'monthly',
                'loan_term': app.loan_term or 12,
            })

        return JsonResponse({
            'success': True,
            'applications': applications_data,
            'count': len(applications_data)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'applications': []
        }, status=200)


@login_required
def member_loans_api(request):
    """API endpoint for member's active loans"""
    try:
        # Check if user has member profile
        if not hasattr(request.user, 'member_profile'):
            return JsonResponse({
                'success': False,
                'error': 'Member profile not found',
                'loans': []
            })

        member = request.user.member_profile

        # Get loans for this member
        loans = Loan.objects.filter(member=member).order_by('-disbursement_date')

        # Build response data
        loans_data = []
        today = date.today()

        for loan in loans:
            # Calculate penalty if overdue
            penalty = 0
            days_overdue = 0
            if loan.due_date and loan.due_date < today and loan.status == 'active':
                days_overdue = (today - loan.due_date).days
                if days_overdue > 360:
                    penalty_months = ((days_overdue - 360) + 29) // 30
                    penalty = float(loan.remaining_balance or 0) * 0.02 * penalty_months

            # Calculate progress percentage
            progress = 0
            if loan.amount and loan.amount > 0:
                progress = (float(loan.paid_amount or 0) / float(loan.amount)) * 100

            loans_data.append({
                'id': loan.id,
                'loan_number': loan.loan_number,
                'loan_type': loan.loan_product.name if loan.loan_product else 'APCP',
                'principal': float(loan.amount),
                'monthly_payment': float(loan.monthly_payment),
                'remaining_balance': float(loan.remaining_balance),
                'paid_amount': float(loan.paid_amount or 0),
                'progress': round(progress, 1),
                'penalty': round(penalty, 2),
                'days_overdue': days_overdue,
                'status': loan.status,
                'next_due_date': loan.due_date.strftime('%Y-%m-%d') if loan.due_date else None,
                'disbursement_date': loan.disbursement_date.strftime('%Y-%m-%d') if loan.disbursement_date else None,
            })

        return JsonResponse({
            'success': True,
            'loans': loans_data,
            'count': len(loans_data)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'loans': []
        })


@login_required
def member_payments_api(request):
    """API endpoint for member's payment history"""
    try:
        # Check if user has member profile
        if not hasattr(request.user, 'member_profile'):
            return JsonResponse({
                'success': False,
                'error': 'Member profile not found',
                'payments': []
            })

        member = request.user.member_profile

        # Get payments for this member
        payments = Payment.objects.filter(member=member, is_posted=True).order_by('-payment_date')

        # Build response data
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment.id,
                'payment_number': payment.payment_number,
                'receipt_number': payment.payment_number,
                'loan_number': payment.loan.loan_number if payment.loan else 'N/A',
                'amount': float(payment.amount),
                'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
                'payment_method': payment.payment_method,
                'principal_amount': float(payment.principal_amount) if payment.principal_amount else 0,
                'interest_amount': float(payment.interest_amount) if payment.interest_amount else 0,
                'penalty_amount': float(payment.penalty_amount) if payment.penalty_amount else 0,
                'receipt_url': f'/api/payment-receipt/{payment.id}/' if payment.id else None,
            })

        return JsonResponse({
            'success': True,
            'payments': payments_data,
            'count': len(payments_data)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'payments': []
        })


@login_required
def notifications_api(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    data = {
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'link': n.link,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
        } for n in notifications]
    }
    return JsonResponse(data)


@login_required
def mark_notification_read_api(request, notif_id):
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read_api(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def delete_notification_api(request, notif_id):
    if request.method == 'DELETE':
        notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def notifications_page(request):
    return render(request, 'main/notifications.html')


@login_required
def member_analytics_api(request):
    try:
        member = request.user.member_profile

        payment_labels = []
        payment_data = []

        today = date.today()
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            month_name = month_date.strftime('%b %Y')
            payment_labels.append(month_name)

            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)

            monthly_payments = Payment.objects.filter(
                member=member,
                payment_date__gte=month_start,
                payment_date__lt=next_month,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0
            payment_data.append(float(monthly_payments))

        # FIXED: changed 'borrower' to 'member'
        loans = Loan.objects.filter(member=member)
        distribution_labels = []
        distribution_data = []

        loan_type_counts = {}
        for loan in loans:
            loan_type = loan.loan_product.name if loan.loan_product else 'APCP'
            loan_type_counts[loan_type] = loan_type_counts.get(loan_type, 0) + 1

        distribution_labels = list(loan_type_counts.keys())
        distribution_data = list(loan_type_counts.values())

        return JsonResponse({
            'payment_labels': payment_labels,
            'payment_data': payment_data,
            'distribution_labels': distribution_labels,
            'distribution_data': distribution_data,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})


@login_required
def payment_receipt_api(request, payment_id):
    """Generate PDF receipt for a payment"""
    try:
        payment = get_object_or_404(Payment, id=payment_id, member=request.user.member_profile)

        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="receipt_{payment.payment_number}.pdf"'

        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        # Header
        p.setFont("Helvetica-Bold", 24)
        p.drawString(180, height - 50, "TOMPuCO COOPERATIVE")
        p.setFont("Helvetica-Bold", 16)
        p.drawString(220, height - 80, "OFFICIAL RECEIPT")

        # Details
        p.setFont("Helvetica", 11)
        y = height - 120
        p.drawString(50, y, f"Receipt Number: {payment.payment_number}")
        p.drawString(50, y - 20, f"Date: {payment.payment_date.strftime('%B %d, %Y')}")
        p.drawString(50, y - 40, f"Member: {payment.member.first_name} {payment.member.last_name}")
        p.drawString(50, y - 60, f"Loan Number: {payment.loan.loan_number}")

        p.line(50, y - 75, width - 50, y - 75)

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y - 100, "PAYMENT DETAILS")
        p.setFont("Helvetica", 11)
        p.drawString(50, y - 120, f"Amount Paid: ₱{payment.amount:,.2f}")
        p.drawString(50, y - 140, f"Payment Method: {payment.get_payment_method_display()}")
        p.drawString(50, y - 160, f"Principal: ₱{payment.principal_amount:,.2f}")
        p.drawString(50, y - 180, f"Interest: ₱{payment.interest_amount:,.2f}")

        if payment.penalty_amount and payment.penalty_amount > 0:
            p.drawString(50, y - 200, f"Penalty: ₱{payment.penalty_amount:,.2f}")

        p.line(50, y - 220, width - 50, y - 220)
        p.drawString(50, y - 240, f"Remaining Balance: ₱{payment.remaining_balance_after:,.2f}")

        p.setFont("Helvetica-Oblique", 10)
        p.drawString(180, 50, "Thank you for your payment!")
        p.drawString(160, 35, "This is a system-generated receipt.")

        p.showPage()
        p.save()

        return response

    except Exception as e:
        return HttpResponse(f"Error generating receipt: {str(e)}", status=500)


@login_required
def member_stats_api(request):
    try:
        member = request.user.member_profile

        # FIXED: changed 'borrower' to 'member' and 'principal_amount' to 'amount'
        loans = Loan.objects.filter(member=member)
        total_loaned = loans.aggregate(total=Sum('amount'))['total'] or 0
        active_loans_count = loans.filter(status='active').count()
        total_paid = Payment.objects.filter(member=member, status='completed').aggregate(total=Sum('amount'))[
                         'total'] or 0
        total_remaining_balance = loans.aggregate(total=Sum('remaining_balance'))['total'] or 0
        pending_applications = LoanApplication.objects.filter(member=member, status='pending_staff_review').count()

        next_due = None
        active_loan = loans.filter(status='active').first()
        if active_loan and active_loan.due_date:
            next_due = active_loan.due_date.isoformat()

        return JsonResponse({
            'total_loaned': float(total_loaned),
            'active_loans_count': active_loans_count,
            'total_paid': float(total_paid),
            'total_remaining_balance': float(total_remaining_balance),
            'pending_applications': pending_applications,
            'next_due_date': next_due,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)})


@login_required
def loan_payment_schedule_api(request, loan_id):
    try:
        member = request.user.member_profile
        # FIXED: changed 'borrower' to 'member'
        loan = get_object_or_404(Loan, id=loan_id, member=member)

        schedule = []
        balance = float(loan.remaining_balance)
        monthly_payment = float(loan.monthly_payment)
        interest_rate = float(loan.interest_rate)
        term_months = loan.term_months
        monthly_rate = interest_rate / 100 / term_months

        from datetime import date, timedelta
        next_date = loan.due_date or (loan.disbursement_date + timedelta(days=30))

        for i in range(term_months):
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            if principal > balance:
                principal = balance
                monthly_payment = interest + principal

            balance = balance - principal

            schedule.append({
                'month': i + 1,
                'due_date': next_date.strftime('%Y-%m-%d'),
                'payment_amount': round(monthly_payment, 2),
                'interest': round(interest, 2),
                'principal': round(principal, 2),
                'balance': round(max(0, balance), 2),
                'status': 'pending'
            })

            next_date = next_date + timedelta(days=30)
            if balance <= 0:
                break

        return JsonResponse({'schedule': schedule})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ============================================================
# 2FA VIEWS FOR MEMBERS
# ============================================================

@login_required
def setup_2fa(request):
    member_profile = request.user.member_profile

    if request.method == 'POST':
        device = TOTPDevice.objects.filter(user=request.user).first()
        if not device:
            device = TOTPDevice.objects.create(
                user=request.user,
                name='Member 2FA',
                confirmed=False
            )

        otp_code = request.POST.get('otp_code', '')
        if device.verify_token(otp_code):
            device.confirmed = True
            device.save()

            member_profile.otp_enabled = True
            member_profile.otp_enabled_at = timezone.now()
            member_profile.otp_secret = device.bin_key.hex()

            backup_codes = []
            for i in range(10):
                code = secrets.token_hex(4).upper()
                formatted_code = f"{code[:5]}-{code[5:]}"
                backup_codes.append(formatted_code)
            member_profile.otp_backup_codes = backup_codes
            member_profile.save()

            messages.success(request, 'Two-Factor Authentication enabled successfully!')
            return redirect('main:member_profile')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
            return redirect('main:setup_2fa')

    device = TOTPDevice.objects.filter(user=request.user).first()
    if not device:
        device = TOTPDevice.objects.create(
            user=request.user,
            name='Member 2FA',
            confirmed=False
        )

    provisioning_uri = device.config_url

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    context = {
        'member': request.user.member_profile,
        'qr_code': qr_base64,
        'secret_key': device.bin_key.hex(),
        'provisioning_uri': provisioning_uri,
    }

    return render(request, 'main/setup_2fa.html', context)


@login_required
def disable_2fa(request):
    if request.method == 'POST':
        member_profile = request.user.member_profile
        TOTPDevice.objects.filter(user=request.user).delete()

        member_profile.otp_enabled = False
        member_profile.otp_secret = None
        member_profile.otp_backup_codes = []
        member_profile.save()

        messages.success(request, 'Two-Factor Authentication has been disabled.')
        return redirect('main:member_profile')

    return redirect('main:member_profile')


@login_required
def generate_backup_codes(request):
    if request.method == 'POST':
        member_profile = request.user.member_profile

        if not member_profile.otp_enabled:
            messages.error(request, '2FA is not enabled. Please enable it first.')
            return redirect('main:setup_2fa')

        new_backup_codes = []
        for i in range(10):
            code = secrets.token_hex(4).upper()
            formatted_code = f"{code[:5]}-{code[5:]}"
            new_backup_codes.append(formatted_code)

        member_profile.otp_backup_codes = new_backup_codes
        member_profile.save()

        messages.success(request, 'New backup codes generated!')
        return redirect('main:member_profile')

    return redirect('main:member_profile')


@login_required
def verify_2fa_login(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '')
        user = request.user

        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device and device.verify_token(otp_code):
            request.session['2fa_verified'] = True
            return redirect(request.GET.get('next', 'main:dashboard'))

        member_profile = user.member_profile
        if otp_code in member_profile.otp_backup_codes:
            codes = member_profile.otp_backup_codes
            codes.remove(otp_code)
            member_profile.otp_backup_codes = codes
            member_profile.save()
            request.session['2fa_verified'] = True
            return redirect(request.GET.get('next', 'main:dashboard'))

        messages.error(request, 'Invalid 2FA code. Please try again.')

    return render(request, 'main/verify_2fa.html')

def verification_rejected(request):
    """Verification rejected page"""
    return render(request, 'main/verification_rejected.html')


def account_suspended(request):
    """Account suspended page"""
    return render(request, 'main/account_suspended.html')