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
from decimal import Decimal
import json
import random
import base64
from datetime import datetime, timedelta, date
from django.db import models
from django.db.models import Sum, Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils.dateparse import parse_date
import csv
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import io
import base64
import secrets
from io import StringIO, BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

from main.forms import MemberRegistrationForm
from main.notification_helper import create_notification, get_user_notifications, get_unread_count
from main.models import (
    Member, Loan, LoanApplication, LoanProduct,
    Payment, PaymentSchedule, Notification, MemberDocument,
    CommitteeDecision, AuditLog, SystemSetting, PaymentReceipt, PaymentReminder
)

# OTP storage
otp_storage = {}


# ============================================================
# QR CODE GENERATION FUNCTION
# ============================================================

def generate_member_qr_code(member):
    """Generate QR code for member"""
    # Create QR code data (Member ID)
    qr_data = member.membership_number

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Create image with brand color
    img = qr.make_image(fill_color="#0d6e6e", back_color="white")

    # Convert to base64 for embedding in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return img_str


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
            return redirect('staff:staff_dashboard')
        return redirect('/')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            if user.is_staff or hasattr(user, 'staff_profile'):
                return redirect('staff:staff_dashboard')
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
            if user.is_superuser:
                return redirect('/superadmin/')
            elif user.groups.filter(name='Manager').exists():
                return redirect('manager:dashboard')
            elif user.groups.filter(name='Committee').exists():
                return redirect('committee:dashboard')
            elif user.groups.filter(name='Cashier').exists():
                return redirect('cashier:dashboard')
            elif user.is_staff:
                return redirect('staff:staff_dashboard')
            else:
                return redirect('main:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser:
            return reverse_lazy('admin_panel:dashboard')
        elif user.groups.filter(name='Manager').exists():
            return reverse_lazy('manager:dashboard')
        elif user.groups.filter(name='Committee').exists():
            return reverse_lazy('committee:dashboard')
        elif user.groups.filter(name='Cashier').exists():
            return reverse_lazy('cashier:dashboard')
        elif user.is_staff:
            return reverse_lazy('staff:staff_dashboard')
        else:
            return reverse_lazy('main:dashboard')


def landing_page(request):
    return render(request, 'main/landing.html')


def custom_logout(request):
    logout(request)
    return redirect('/')


def register(request):
    if request.user.is_authenticated:
        return redirect('main:dashboard')

    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Member.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                contact_number=form.cleaned_data.get('contact_number', ''),
                residence_address=form.cleaned_data.get('residence_address', ''),
                is_active=True
            )
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('main:login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = MemberRegistrationForm()

    return render(request, 'main/register.html', {'form': form})


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
    if request.user.is_superuser:
        return redirect('/superadmin/')
    if request.user.is_staff:
        return redirect('/staff/dashboard/')

    user = request.user

    if user.groups.filter(name='Committee').exists():
        return redirect('committee:committee_dashboard')
    if user.groups.filter(name='Cashier').exists():
        return redirect('cashier:dashboard')
    if user.groups.filter(name='Manager').exists():
        return redirect('manager:dashboard')

    try:
        member = user.member_profile
        loans = Loan.objects.filter(borrower=member)
        total_loaned = loans.aggregate(total=Sum('principal_amount'))['total'] or Decimal(0)
        active_loans = loans.filter(status='active')
        total_paid = Payment.objects.filter(member=member, status='completed').aggregate(total=Sum('amount'))[
                         'total'] or Decimal(0)
        applications = LoanApplication.objects.filter(member=member).order_by('-created_at')[:5]
        pending_applications = LoanApplication.objects.filter(member=member, status='pending_staff_review').count()
        profile_completeness = calculate_profile_completeness(member)
        unread_count = get_unread_count(user)

        total_remaining = active_loans.aggregate(total=Sum('remaining_balance'))['total'] or Decimal(0)

        next_due = None
        for loan in active_loans:
            if loan.next_due_date:
                if not next_due or loan.next_due_date < next_due:
                    next_due = loan.next_due_date

        # Generate QR code for member
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
            'qr_image': qr_image,  # Add QR code to context
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
        total_loans = Loan.objects.filter(borrower=member).count()
        total_borrowed = Loan.objects.filter(borrower=member, status='paid').aggregate(
            total=Sum('principal_amount'))['total'] or Decimal(0)
        comaker_loans = Loan.objects.filter(co_maker=member, status='active').count()

        # Generate QR code
        qr_image = generate_member_qr_code(member)

        return render(request, 'main/member_profile.html', {
            'member': member,
            'profile_completeness': profile_completeness,
            'documents_count': documents_count,
            'total_loans': total_loans,
            'total_borrowed': total_borrowed,
            'comaker_loans': comaker_loans,
            'qr_image': qr_image,  # Add QR code to context
        })
    except Member.DoesNotExist:
        messages.warning(request, 'Please complete your profile first.')
        return redirect('main:edit_profile')


@login_required
def member_qr_code(request):
    """Display member's QR code for scanning"""
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
    """Edit member profile - UPDATED to handle profile picture uploads"""
    member = request.user.member_profile

    if request.method == 'POST':
        try:
            # Helper function to clean string values
            def clean_string(value, max_length=None):
                if value is None or value == 'None' or value == 'null' or value == '':
                    return ''
                value = str(value).strip()
                if max_length and len(value) > max_length:
                    value = value[:max_length]
                return value

            # Get form data with cleaning
            first_name = clean_string(request.POST.get('first_name', ''))
            last_name = clean_string(request.POST.get('last_name', ''))
            middle_initial = clean_string(request.POST.get('middle_initial', ''), max_length=1)
            nickname = clean_string(request.POST.get('nickname', ''))
            nationality = request.POST.get('nationality', 'Filipino')
            if nationality == 'None':
                nationality = 'Filipino'

            birthdate = request.POST.get('birthdate')
            if birthdate == 'None' or birthdate == '':
                birthdate = None

            gender = request.POST.get('gender', '')
            if gender == 'None':
                gender = ''

            age = request.POST.get('age', 0)
            if age == 'None' or age == '':
                age = 0
            else:
                age = int(age)

            contact_number = clean_string(request.POST.get('contact_number', ''))
            residence_address = clean_string(request.POST.get('residence_address', ''))
            spouse_name = clean_string(request.POST.get('spouse_name', ''))

            num_dependents = request.POST.get('num_dependents', 0)
            if num_dependents == 'None' or num_dependents == '':
                num_dependents = 0
            else:
                num_dependents = int(num_dependents)

            farm_location = clean_string(request.POST.get('farm_location', ''))

            # Handle profile picture upload - FIXED
            if request.FILES.get('profile_picture'):
                # Delete old profile picture if exists
                if member.profile_picture:
                    try:
                        member.profile_picture.delete(save=False)
                    except:
                        pass
                # Save new profile picture
                member.profile_picture = request.FILES['profile_picture']

            # Handle remove profile picture
            if request.POST.get('remove_profile_picture') == 'on':
                if member.profile_picture:
                    try:
                        member.profile_picture.delete(save=False)
                    except:
                        pass
                    member.profile_picture = None

            # Update user
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            # Update member
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

            if birthdate:
                from datetime import datetime
                member.birthdate = datetime.strptime(birthdate, '%Y-%m-%d').date()

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
    """Upload profile picture"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        try:
            member = request.user.member_profile

            # Delete old profile picture if exists
            if member.profile_picture:
                try:
                    member.profile_picture.delete(save=False)
                except:
                    pass

            # Save new profile picture
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
        has_active_loan = Loan.objects.filter(borrower=member, status='active').exists()
        available_comakers = Member.objects.filter(is_active=True).exclude(id=member.id)[:10]

        context = {
            'member': member,
            'loan_products': loan_products,
            'has_active_loan': has_active_loan,
            'available_comakers': available_comakers,
            'profile_completeness': calculate_profile_completeness(member),
        }
        return render(request, 'main/apply_loan.html', context)
    except Member.DoesNotExist:
        messages.error(request, 'Please complete your profile first.')
        return redirect('main:edit_profile')


@login_required
def submit_loan_application(request):
    if request.method == 'POST':
        if not request.session.get('otp_verified'):
            return JsonResponse({'success': False, 'error': 'OTP verification required.'})

        try:
            member = request.user.member_profile
        except Member.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Member profile not found'})

        amount = Decimal(request.POST.get('amount', 0))
        purpose = request.POST.get('purpose', '')
        collateral = request.POST.get('collateral', '')
        mode_of_payment = request.POST.get('mode_of_payment', 'monthly')
        term = int(request.POST.get('term', 12))
        co_maker_id = request.POST.get('co_maker_id')
        loan_product_id = request.POST.get('loan_product_id')

        loan_product = get_object_or_404(LoanProduct, id=loan_product_id) if loan_product_id else None

        if amount < 1000:
            return JsonResponse({'success': False, 'error': 'Minimum loan amount is ₱1,000.'})
        if not purpose:
            return JsonResponse({'success': False, 'error': 'Please provide a loan purpose.'})

        if loan_product:
            if amount < loan_product.min_amount:
                return JsonResponse(
                    {'success': False, 'error': f'Minimum amount for this product is ₱{loan_product.min_amount:,.2f}'})
            if amount > loan_product.max_amount:
                return JsonResponse(
                    {'success': False, 'error': f'Maximum amount for this product is ₱{loan_product.max_amount:,.2f}'})

        interest_rate = loan_product.interest_rate if loan_product else Decimal('20')
        monthly_rate = (interest_rate / 100) / 12

        if monthly_rate > 0:
            monthly_payment = (amount * monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
        else:
            monthly_payment = amount / term

        total_payable = monthly_payment * term
        total_interest = total_payable - amount

        service_charge = amount * Decimal('0.02')
        cbu_retention = amount * Decimal('0.01')
        insurance_charge = amount * Decimal('0.005')
        service_fee = Decimal('35')
        notarial_fee = Decimal('200')

        total_deductions = service_charge + cbu_retention + insurance_charge + service_fee + notarial_fee
        net_proceeds = amount - total_deductions

        if request.FILES.get('collateral_document'):
            member.collateral_document = request.FILES['collateral_document']
            member.collateral_document_type = request.POST.get('collateral_document_type', '')
            member.collateral_document_number = request.POST.get('collateral_document_number', '')
            member.collateral_issued_by = request.POST.get('collateral_issued_by', '')
            member.collateral_property_description = request.POST.get('collateral_property_description', '')
            if request.POST.get('collateral_area'):
                member.collateral_area = Decimal(request.POST.get('collateral_area'))
            member.save()

        application = LoanApplication.objects.create(
            member=member,
            co_maker_id=int(co_maker_id) if co_maker_id else None,
            applicant_user=request.user,
            loan_product=loan_product,
            requested_amount=amount,
            purpose=purpose,
            collateral_offered=collateral,
            mode_of_payment=mode_of_payment,
            loan_term=term,
            interest_rate=interest_rate,
            total_interest=total_interest,
            monthly_payment=monthly_payment,
            total_payable=total_payable,
            service_charge=service_charge,
            cbu_retention=cbu_retention,
            insurance_charge=insurance_charge,
            service_fee=service_fee,
            notarial_fee=notarial_fee,
            total_deductions=total_deductions,
            net_proceeds=net_proceeds,
            status='pending_staff_review'
        )

        request.session.pop('otp_verified', None)
        if request.user.id in otp_storage:
            del otp_storage[request.user.id]

        create_notification(
            recipient=request.user,
            notification_type='application',
            title='Loan Application Submitted',
            message=f'Your loan application for ₱{amount:,.2f} has been submitted.',
            link=f'/main/application/{application.id}/'
        )

        from django.contrib.auth.models import User
        staff_users = User.objects.filter(is_staff=True)
        for staff in staff_users:
            create_notification(
                recipient=staff,
                notification_type='application',
                title='New Loan Application',
                message=f'New loan application from {member.first_name} {member.last_name} for ₱{amount:,.2f}',
                link=f'/staff/applications/{application.id}/'
            )

        log_audit(request.user, 'create', 'LoanApplication', application.id, request=request)

        return JsonResponse({
            'success': True,
            'application_id': application.id,
            'application_number': application.application_id
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


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

            active_loans_as_comaker = Loan.objects.filter(co_maker=co_maker, status='active').count()
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
        active_loans_as_comaker = Loan.objects.filter(co_maker=co_maker, status='active').count()
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
        data = json.loads(request.body)
        signature_data = data.get('signature')
        try:
            member = request.user.member_profile
            member.signature = signature_data
            member.save()
            log_audit(request.user, 'update', 'Member', member.id, request=request)
            return JsonResponse({'success': True, 'message': 'Signature saved.'})
        except Member.DoesNotExist:
            return JsonResponse({'error': 'Member profile not found'}, status=404)


# ============================================================
# LOAN AND APPLICATION VIEWS
# ============================================================

@login_required
def my_applications(request):
    try:
        applications = LoanApplication.objects.filter(member=request.user.member_profile).order_by('-created_at')
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
        loans = Loan.objects.filter(borrower=request.user.member_profile).order_by('-created_at')
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
                (loan.total_paid / loan.total_payable_amount) * 100) if loan.total_payable_amount > 0 else 0
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

        # Import LoanAttachment
        try:
            from main.models import LoanAttachment
            attachments = LoanAttachment.objects.filter(loan_application=application)
        except:
            attachments = []

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
            'attachments': attachments,
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
        loan = get_object_or_404(Loan, id=loan_id, borrower=request.user.member_profile)
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
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

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
        active_loans = Loan.objects.filter(borrower=member, status='active')
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
    """FAQ Chatbot API"""
    if request.method == 'POST':
        try:
            import json
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
# ADD MISSING IMPORTS
# ============================================================
try:
    from main.models import LoanAttachment
except ImportError:
    LoanAttachment = None


# ============================================================
# LOAN TYPES VIEW
# ============================================================

@login_required
def loan_types(request):
    """Display all loan products with Apply Now buttons"""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        member = None

    context = {
        'member': member,
    }
    return render(request, 'main/loan_types.html', context)


# ============================================================
# API VIEWS FOR MEMBER DATA
# ============================================================

@login_required
def member_applications_api(request):
    """API endpoint to get member's loan applications"""
    try:
        member = request.user.member_profile
        applications = LoanApplication.objects.filter(member=member).order_by('-created_at')

        data = {
            'applications': [{
                'id': app.id,
                'application_id': app.application_id,
                'loan_type': app.loan_product.display_name if app.loan_product else 'APCP',
                'requested_amount': float(app.requested_amount),
                'approved_line': float(app.approved_line) if app.approved_line else None,
                'status': app.status,
                'date_applied': app.date_applied.isoformat() if app.date_applied else None,
                'purpose': app.purpose,
                'collateral_offered': app.collateral_offered,
                'mode_of_payment': app.mode_of_payment,
                'loan_term': app.loan_term,
                'committee_remarks': app.committee_remarks,
                'manager_remarks': app.manager_remarks,
            } for app in applications]
        }
        return JsonResponse(data)
    except Member.DoesNotExist:
        return JsonResponse({'applications': []})
    except Exception as e:
        return JsonResponse({'applications': [], 'error': str(e)})


@login_required
def member_loans_api(request):
    """API endpoint to get member's loans"""
    try:
        member = request.user.member_profile
        loans = Loan.objects.filter(borrower=member).order_by('-disbursement_date')

        data = {
            'loans': [{
                'id': loan.id,
                'loan_number': loan.loan_number,
                'loan_type': loan.loan_product.name if loan.loan_product else 'APCP',
                'principal_amount': float(loan.principal_amount),
                'monthly_payment': float(loan.monthly_payment),
                'remaining_balance': float(loan.remaining_balance),
                'total_paid': float(loan.paid_amount),
                'total_payable_amount': float(loan.total_payable_amount),
                'status': loan.status,
                'disbursement_date': loan.disbursement_date.isoformat() if loan.disbursement_date else None,
                'next_due_date': loan.next_due_date.isoformat() if loan.next_due_date else None,
            } for loan in loans]
        }
        return JsonResponse(data)
    except Member.DoesNotExist:
        return JsonResponse({'loans': []})
    except Exception as e:
        return JsonResponse({'loans': [], 'error': str(e)})


@login_required
def member_payments_api(request):
    """API endpoint to get member's payment history"""
    try:
        member = request.user.member_profile
        payments = Payment.objects.filter(member=member, is_posted=True).order_by('-payment_date')

        data = {
            'payments': [{
                'id': payment.id,
                'payment_number': payment.payment_number,
                'receipt_number': payment.receipt.receipt_number if hasattr(payment, 'receipt') else None,
                'loan_number': payment.loan.loan_number,
                'amount': float(payment.amount),
                'principal_amount': float(payment.principal_amount),
                'interest_amount': float(payment.interest_amount),
                'penalty_amount': float(payment.penalty_amount),
                'payment_method': payment.payment_method,
                'payment_date': payment.payment_date.isoformat(),
                'receipt_url': payment.receipt.receipt_pdf.url if hasattr(payment,
                                                                          'receipt') and payment.receipt.receipt_pdf else None,
            } for payment in payments]
        }
        return JsonResponse(data)
    except Member.DoesNotExist:
        return JsonResponse({'payments': []})
    except Exception as e:
        return JsonResponse({'payments': [], 'error': str(e)})


@login_required
def notifications_api(request):
    """API endpoint to get user notifications"""
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
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@login_required
def mark_all_notifications_read_api(request):
    """Mark all notifications as read"""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
def delete_notification_api(request, notif_id):
    """Delete a notification"""
    if request.method == 'DELETE':
        notification = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def notifications_page(request):
    """Notifications page for members"""
    return render(request, 'main/notifications.html')


@login_required
def member_analytics_api(request):
    """API endpoint for member analytics data"""
    try:
        member = request.user.member_profile

        # Get last 6 months payment data
        from datetime import date, timedelta
        payment_labels = []
        payment_data = []

        today = date.today()
        for i in range(5, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=i * 30)
            month_name = month_date.strftime('%b %Y')
            payment_labels.append(month_name)

            # Calculate total payments for that month
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

        # Get loan distribution by type
        loans = Loan.objects.filter(borrower=member)
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
def member_stats_api(request):
    """API endpoint for member statistics"""
    try:
        member = request.user.member_profile

        loans = Loan.objects.filter(borrower=member)
        total_loaned = loans.aggregate(total=Sum('principal_amount'))['total'] or 0
        active_loans_count = loans.filter(status='active').count()
        total_paid = Payment.objects.filter(member=member, status='completed').aggregate(total=Sum('amount'))[
                         'total'] or 0
        total_remaining_balance = loans.aggregate(total=Sum('remaining_balance'))['total'] or 0
        pending_applications = LoanApplication.objects.filter(member=member, status='pending_staff_review').count()

        next_due = None
        active_loan = loans.filter(status='active').first()
        if active_loan and active_loan.next_due_date:
            next_due = active_loan.next_due_date.isoformat()

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
    """API endpoint to get loan payment schedule"""
    try:
        member = request.user.member_profile
        loan = get_object_or_404(Loan, id=loan_id, borrower=member)

        # Generate payment schedule
        schedule = []
        balance = float(loan.remaining_balance)
        monthly_payment = float(loan.monthly_payment)
        interest_rate = float(loan.interest_rate)
        term_months = loan.term_months
        monthly_rate = interest_rate / 100 / term_months

        from datetime import date, timedelta
        next_date = loan.next_due_date or (loan.disbursement_date + timedelta(days=30))

        for i in range(term_months):
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            if principal > balance:
                principal = balance
                monthly_payment = interest + principal

            balance = balance - principal

            # Determine status based on due date and payments
            status = 'pending'

            schedule.append({
                'month': i + 1,
                'due_date': next_date.strftime('%Y-%m-%d'),
                'payment_amount': round(monthly_payment, 2),
                'interest': round(interest, 2),
                'principal': round(principal, 2),
                'balance': round(max(0, balance), 2),
                'status': status
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
    """Setup Two-Factor Authentication for member"""
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

            # Generate backup codes
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

    # GET request - show setup form
    device = TOTPDevice.objects.filter(user=request.user).first()
    if not device:
        device = TOTPDevice.objects.create(
            user=request.user,
            name='Member 2FA',
            confirmed=False
        )

    provisioning_uri = device.config_url

    # Generate QR code
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
    """Disable Two-Factor Authentication for member"""
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
    """Generate new backup codes for 2FA"""
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
    """Verify 2FA code during login"""
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