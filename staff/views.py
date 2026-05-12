from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from datetime import datetime, timedelta
import json
from django.views.decorators.csrf import csrf_exempt
import qrcode
import io
import base64
import secrets
from decimal import Decimal
from django.http import JsonResponse
from main.models import Payment, Member, Loan
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count, Q


# 2FA imports
from django_otp.plugins.otp_totp.models import TOTPDevice

# Import models from main.models (only the models that actually exist)
from main.models import (
    Member, LoanProduct, LoanApplication, Loan, Payment,
    PaymentSchedule, MemberDocument, Notification, AuditLog,
    CommitteeDecision, SystemSetting
)

# Import staff models
from .models import StaffProfile, StaffActivityLog, PaymentInstruction, RestructuringRequest, StaffNotification


# ==================== HELPER FUNCTIONS ====================

def is_staff(user):
    """Check if user has staff role"""
    return user.is_authenticated and hasattr(user, 'staff_profile')


def log_activity(staff, action, entity_type, entity_id, request):
    """Helper to log staff activities"""
    StaffActivityLog.objects.create(
        staff=staff,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )


# ==================== DASHBOARD VIEWS ====================

@login_required
@user_passes_test(is_staff)
def dashboard(request):
    """Staff dashboard with real-time analytics"""
    staff_profile = request.user.staff_profile

    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q
    from main.models import LoanApplication, Loan, Payment, Member

    # ============================================================
    # LOAN APPLICATION STATISTICS
    # ============================================================
    total_applications = LoanApplication.objects.count()
    pending_count = LoanApplication.objects.filter(status='pending_staff_review').count()
    committee_count = LoanApplication.objects.filter(status='with_committee').count()
    line_approved_count = LoanApplication.objects.filter(status='line_approved').count()
    approved_count = LoanApplication.objects.filter(status='manager_approved').count()
    rejected_count = LoanApplication.objects.filter(status='rejected').count()
    ready_for_disbursement = LoanApplication.objects.filter(status='ready_for_disbursement').count()
    disbursed_count = LoanApplication.objects.filter(status='disbursed').count()

    # ============================================================
    # LOAN STATISTICS
    # ============================================================
    active_loans = Loan.objects.filter(status='active').count()
    overdue_loans = Loan.objects.filter(status='overdue').count()
    paid_loans = Loan.objects.filter(status='paid').count()
    restructured_loans = Loan.objects.filter(status='restructured').count()
    total_loans = Loan.objects.count()

    # Total principal amount
    total_principal = Loan.objects.aggregate(total=Sum('principal_amount'))['total'] or 0
    total_remaining_balance = Loan.objects.aggregate(total=Sum('remaining_balance'))['total'] or 0
    total_paid = Loan.objects.aggregate(total=Sum('paid_amount'))['total'] or 0

    # Calculate collection rate
    collection_rate = 0
    if total_principal > 0:
        collection_rate = (float(total_paid) / float(total_principal)) * 100

    # ============================================================
    # COLLECTION DATA (Last 7 days)
    # ============================================================
    today = date.today()
    collection_labels = []
    collection_data = []

    for i in range(6, -1, -1):
        dt = today - timedelta(days=i)
        collection_labels.append(dt.strftime('%a, %b %d'))
        daily_total = Payment.objects.filter(
            payment_date=dt,
            is_posted=True
        ).aggregate(total=Sum('amount'))['total'] or 0
        collection_data.append(float(daily_total))

    # Weekly, Monthly, Yearly collections
    week_start = today - timedelta(days=7)
    month_start = today - timedelta(days=30)
    year_start = today - timedelta(days=365)

    week_collection = Payment.objects.filter(
        payment_date__gte=week_start,
        is_posted=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    month_collection = Payment.objects.filter(
        payment_date__gte=month_start,
        is_posted=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    year_collection = Payment.objects.filter(
        payment_date__gte=year_start,
        is_posted=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    today_collection = Payment.objects.filter(
        payment_date=today,
        is_posted=True
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ============================================================
    # LOAN DISTRIBUTION BY TYPE
    # ============================================================
    loan_types = ['APCP', 'NCL', 'SALARY', 'COLLATERAL', 'TRADE', 'B2B', 'PROVIDENTIAL']
    distribution_labels = []
    distribution_data = []

    for loan_type in loan_types:
        count = Loan.objects.filter(loan_product__loan_type=loan_type).count()
        if count > 0:
            distribution_labels.append(loan_type)
            distribution_data.append(count)

    # If no loans yet, show sample data
    if not distribution_data:
        distribution_labels = ['APCP', 'NCL', 'SALARY', 'COLLATERAL']
        distribution_data = [0, 0, 0, 0]

    # ============================================================
    # STATUS DISTRIBUTION FOR APPLICATIONS
    # ============================================================
    status_labels = ['Pending', 'Committee', 'Line Approved', 'Approved', 'Rejected', 'Ready', 'Disbursed']
    status_data = [
        pending_count,
        committee_count,
        line_approved_count,
        approved_count,
        rejected_count,
        ready_for_disbursement,
        disbursed_count
    ]

    # ============================================================
    # RECENT APPLICATIONS
    # ============================================================
    recent_applications = LoanApplication.objects.select_related('member', 'loan_product').order_by('-date_applied')[:10]

    # Add loan type display
    for app in recent_applications:
        app.loan_type_display = app.loan_product.display_name if app.loan_product else 'N/A'

    # ============================================================
    # RECENT PAYMENTS
    # ============================================================
    recent_payments = Payment.objects.select_related('loan', 'member').filter(is_posted=True).order_by('-payment_date')[:10]

    # ============================================================
    # OVERDUE LOANS
    # ============================================================
    overdue_loans_list = Loan.objects.filter(
        status='overdue',
        next_due_date__lt=today
    ).select_related('borrower')[:5]

    for loan in overdue_loans_list:
        if loan.next_due_date:
            loan.days_overdue = (today - loan.next_due_date).days
        else:
            loan.days_overdue = 0

    # ============================================================
    # UPCOMING DUE DATES (Next 7 days)
    # ============================================================
    upcoming_due = Loan.objects.filter(
        status='active',
        next_due_date__gte=today,
        next_due_date__lte=today + timedelta(days=7)
    ).select_related('borrower')[:5]

    # ============================================================
    # RECENT STAFF ACTIVITIES
    # ============================================================
    recent_activities = StaffActivityLog.objects.filter(
        staff=staff_profile
    ).order_by('-created_at')[:10]

    # ============================================================
    # MEMBER STATISTICS
    # ============================================================
    total_members = Member.objects.filter(is_active=True).count()
    employee_members = Member.objects.filter(is_employee=True, is_active=True).count()
    regular_members = total_members - employee_members

    new_members_this_month = Member.objects.filter(
        created_at__gte=month_start
    ).count()

    # ============================================================
    # RISK METRICS
    # ============================================================
    portfolio_at_risk = 0
    high_risk_count = Loan.objects.filter(status='overdue', next_due_date__lt=today - timedelta(days=30)).count()
    medium_risk_count = Loan.objects.filter(status='overdue', next_due_date__lt=today - timedelta(days=15)).count()
    low_risk_count = active_loans - high_risk_count - medium_risk_count

    if total_loans > 0:
        portfolio_at_risk = (high_risk_count / total_loans) * 100
        high_risk_percentage = (high_risk_count / total_loans) * 100
        medium_risk_percentage = (medium_risk_count / total_loans) * 100
        low_risk_percentage = (low_risk_count / total_loans) * 100
    else:
        high_risk_percentage = medium_risk_percentage = low_risk_percentage = 0

    # Average loan size
    avg_loan_size = 0
    if total_loans > 0:
        avg_loan_size = float(total_principal) / total_loans

    # Default rate
    default_count = Loan.objects.filter(
        Q(status='defaulted') | Q(status='overdue', next_due_date__lt=today - timedelta(days=90))
    ).count()
    default_rate = 0
    if total_loans > 0:
        default_rate = (default_count / total_loans) * 100

    # ============================================================
    # CHART DATA (Monthly trend for last 6 months)
    # ============================================================
    monthly_labels = []
    monthly_applications = []
    monthly_disbursements = []

    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_name = month_date.strftime('%b %Y')
        monthly_labels.append(month_name)

        month_start_date = month_date.replace(day=1)
        if month_date.month == 12:
            next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            next_month = month_date.replace(month=month_date.month + 1, day=1)

        app_count = LoanApplication.objects.filter(
            date_applied__gte=month_start_date,
            date_applied__lt=next_month
        ).count()
        monthly_applications.append(app_count)

        disburse_count = Loan.objects.filter(
            disbursement_date__gte=month_start_date,
            disbursement_date__lt=next_month
        ).count()
        monthly_disbursements.append(disburse_count)

    context = {
        'staff_profile': staff_profile,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'committee_count': committee_count,
        'line_approved_count': line_approved_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'ready_for_disbursement': ready_for_disbursement,
        'disbursed_count': disbursed_count,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'restructured_loans': restructured_loans,
        'paid_loans': paid_loans,
        'total_loans': total_loans,
        'total_principal': total_principal,
        'total_remaining_balance': total_remaining_balance,
        'total_paid': total_paid,
        'collection_rate': round(collection_rate, 2),
        'today_collection': today_collection,
        'week_collection': week_collection,
        'month_collection': month_collection,
        'year_collection': year_collection,
        'collection_labels': json.dumps(collection_labels),
        'collection_data': json.dumps(collection_data),
        'distribution_labels': json.dumps(distribution_labels),
        'distribution_data': json.dumps(distribution_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_applications': json.dumps(monthly_applications),
        'monthly_disbursements': json.dumps(monthly_disbursements),
        'recent_applications': recent_applications,
        'recent_payments': recent_payments,
        'overdue_loans_list': overdue_loans_list,
        'upcoming_due': upcoming_due,
        'recent_activities': recent_activities,
        'total_members': total_members,
        'employee_members': employee_members,
        'regular_members': regular_members,
        'new_members_this_month': new_members_this_month,
        'portfolio_at_risk': round(portfolio_at_risk, 2),
        'avg_loan_size': round(avg_loan_size, 2),
        'default_rate': round(default_rate, 2),
        'high_risk_count': high_risk_count,
        'medium_risk_count': medium_risk_count,
        'low_risk_count': low_risk_count,
        'high_risk_percentage': round(high_risk_percentage, 2),
        'medium_risk_percentage': round(medium_risk_percentage, 2),
        'low_risk_percentage': round(low_risk_percentage, 2),
    }

    return render(request, 'staff/dashboard.html', context)


# ==================== 2FA AUTHENTICATOR VIEWS ====================

@login_required
@user_passes_test(is_staff)
def setup_2fa(request):
    """Setup Two-Factor Authentication for staff"""
    staff_profile = request.user.staff_profile

    if request.method == 'POST':
        device = TOTPDevice.objects.filter(user=request.user).first()
        if not device:
            device = TOTPDevice.objects.create(
                user=request.user,
                name='Default',
                confirmed=False
            )

        otp_code = request.POST.get('otp_code', '')
        if device.verify_token(otp_code):
            device.confirmed = True
            device.save()

            staff_profile.otp_enabled = True
            staff_profile.otp_enabled_at = timezone.now()
            staff_profile.otp_secret = device.bin_key.hex()

            backup_codes = []
            for i in range(10):
                code = secrets.token_hex(4).upper()
                formatted_code = f"{code[:5]}-{code[5:]}"
                backup_codes.append(formatted_code)
            staff_profile.otp_backup_codes = backup_codes
            staff_profile.save()

            messages.success(request, 'Two-Factor Authentication enabled successfully!')
            return redirect('staff:staff_profile')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
            return redirect('staff:setup_2fa')

    device = TOTPDevice.objects.filter(user=request.user).first()
    if not device:
        device = TOTPDevice.objects.create(
            user=request.user,
            name='Default',
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
        'staff_profile': staff_profile,
        'qr_code': qr_base64,
        'secret_key': device.bin_key.hex(),
        'provisioning_uri': provisioning_uri,
    }

    return render(request, 'staff/profile/setup_2fa.html', context)


@login_required
@user_passes_test(is_staff)
def disable_2fa(request):
    """Disable Two-Factor Authentication"""
    if request.method == 'POST':
        staff_profile = request.user.staff_profile
        TOTPDevice.objects.filter(user=request.user).delete()

        staff_profile.otp_enabled = False
        staff_profile.otp_secret = None
        staff_profile.otp_backup_codes = []
        staff_profile.save()

        messages.success(request, 'Two-Factor Authentication has been disabled.')
        return redirect('staff:staff_profile')

    return redirect('staff:staff_profile')


@login_required
@user_passes_test(is_staff)
def generate_backup_codes(request):
    """Generate new backup codes for 2FA"""
    if request.method == 'POST':
        staff_profile = request.user.staff_profile

        if not staff_profile.otp_enabled:
            messages.error(request, '2FA is not enabled. Please enable it first.')
            return redirect('staff:setup_2fa')

        new_backup_codes = []
        for i in range(10):
            code = secrets.token_hex(4).upper()
            formatted_code = f"{code[:5]}-{code[5:]}"
            new_backup_codes.append(formatted_code)

        staff_profile.otp_backup_codes = new_backup_codes
        staff_profile.save()

        messages.success(request, 'New backup codes generated!')

    return redirect('staff:staff_profile')


@login_required
@user_passes_test(is_staff)
def verify_2fa_login(request):
    """Verify 2FA code during login"""
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '')
        user = request.user

        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if device and device.verify_token(otp_code):
            request.session['2fa_verified'] = True
            return redirect(request.GET.get('next', '/staff/dashboard/'))

        staff_profile = user.staff_profile
        if otp_code in staff_profile.otp_backup_codes:
            codes = staff_profile.otp_backup_codes
            codes.remove(otp_code)
            staff_profile.otp_backup_codes = codes
            staff_profile.save()
            request.session['2fa_verified'] = True
            return redirect(request.GET.get('next', '/staff/dashboard/'))

        messages.error(request, 'Invalid 2FA code. Please try again.')

    return render(request, 'staff/profile/verify_2fa.html')


# ==================== APPLICATION VIEWS ====================

@login_required
@user_passes_test(is_staff)
def application_list(request):
    """List all loan applications with filters"""
    staff_profile = request.user.staff_profile

    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    loan_type = request.GET.get('loan_type', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    applications = LoanApplication.objects.select_related('member', 'loan_product').all()

    if search:
        applications = applications.filter(
            Q(application_id__icontains=search) |
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search)
        )

    if status_filter != 'all':
        applications = applications.filter(status=status_filter)

    if loan_type != 'all':
        applications = applications.filter(loan_product__name=loan_type)

    if date_from:
        applications = applications.filter(date_applied__gte=date_from)
    if date_to:
        applications = applications.filter(date_applied__lte=date_to)

    for app in applications:
        app.loan_type = app.loan_product.name if app.loan_product else 'APCP'

    total_applications = applications.count()
    pending_count = applications.filter(status='pending_staff_review').count()
    committee_count = applications.filter(status='with_committee').count()
    line_approved_count = applications.filter(status='line_approved').count()
    approved_count = applications.filter(status='manager_approved').count()
    rejected_count = applications.filter(status='rejected').count()

    loan_products = [
        {'id': 'APCP', 'name': 'APCP - Agricultural Production'},
        {'id': 'NCL', 'name': 'NCL - National Commodity Loan'},
        {'id': 'SALARY', 'name': 'SALARY - Salary Loan'},
        {'id': 'COLLATERAL', 'name': 'COLLATERAL - Collateral Loan'},
        {'id': 'B2B', 'name': 'B2B - Back-to-Back Loan'},
        {'id': 'PROVIDENTIAL', 'name': 'PROVIDENTIAL - Providential Loan'},
        {'id': 'TRADE', 'name': 'TRADE - Trade Loan'},
    ]

    members = Member.objects.filter(is_active=True)[:20]

    context = {
        'staff_profile': staff_profile,
        'applications': applications,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'committee_count': committee_count,
        'line_approved_count': line_approved_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'loan_products': loan_products,
        'members': members,
        'filter_params': request.GET.urlencode(),
    }

    return render(request, 'staff/applications/list.html', context)


@login_required
@user_passes_test(is_staff)
def application_review(request, pk):
    """Review a specific application"""
    staff_profile = request.user.staff_profile
    application = get_object_or_404(LoanApplication, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'verify_documents':
            application.valid_id_verified = True
            application.save()
            messages.success(request, 'Documents verified successfully')

        elif action == 'forward_to_committee':
            application.status = 'with_committee'
            application.staff_remarks = request.POST.get('remarks', '')
            application.save()
            messages.success(request, f'Application forwarded to Committee')

        elif action == 'request_revision':
            application.status = 'needs_revision'
            application.staff_remarks = request.POST.get('revision_reason', '')
            application.save()
            messages.info(request, f'Revision requested')

        elif action == 'reject':
            application.status = 'rejected'
            application.staff_remarks = request.POST.get('reject_reason', '')
            application.save()
            messages.warning(request, f'Application rejected')

        return redirect('staff:staff_applications')

    context = {
        'staff_profile': staff_profile,
        'application': application,
    }

    return render(request, 'staff/applications/review.html', context)


@login_required
@user_passes_test(is_staff)
def add_charges(request, pk):
    """Add charges based on approved line (after manager approval)"""
    staff_profile = request.user.staff_profile
    application = get_object_or_404(LoanApplication, pk=pk)

    if application.status != 'manager_approved':
        messages.error(request, 'Application must be approved by manager before adding charges.')
        return redirect('staff:staff_applications')

    approved_line = float(application.approved_line or 0)

    if request.method == 'POST':
        service_charge = approved_line * 0.03
        cbu_retention = approved_line * 0.02
        insurance = approved_line * 0.0132
        service_fee = 35
        notarial_fee = 200

        inspector_fee = float(request.POST.get('inspector_fee', 0))
        trade_fert = float(request.POST.get('trade_fert', 0))
        ca_int = float(request.POST.get('ca_int', 0))

        total_auto = service_charge + cbu_retention + insurance + service_fee + notarial_fee
        total_optional = inspector_fee + trade_fert + ca_int
        total_deductions = total_auto + total_optional
        net_proceeds = approved_line - total_deductions

        application.service_charge = service_charge
        application.cbu_retention = cbu_retention
        application.insurance_charge = insurance
        application.service_fee = service_fee
        application.notarial_fee = notarial_fee
        application.inspector_fee = inspector_fee
        application.trade_fert = trade_fert
        application.ca_int = ca_int
        application.total_deductions = total_deductions
        application.net_proceeds = net_proceeds
        application.status = 'ready_for_disbursement'
        application.save()

        messages.success(request, f'Charges added. Net Proceeds: ₱{net_proceeds:,.2f}')
        return redirect('staff:staff_applications')

    service_charge = approved_line * 0.03
    cbu_retention = approved_line * 0.02
    insurance = approved_line * 0.0132
    service_fee = 35
    notarial_fee = 200
    total_auto = service_charge + cbu_retention + insurance + service_fee + notarial_fee
    net_proceeds = approved_line - total_auto

    context = {
        'staff_profile': staff_profile,
        'application': application,
        'approved_line': approved_line,
        'service_charge': service_charge,
        'cbu_retention': cbu_retention,
        'insurance': insurance,
        'service_fee': service_fee,
        'notarial_fee': notarial_fee,
        'total_auto': total_auto,
        'net_proceeds': net_proceeds,
    }

    return render(request, 'staff/applications/add_charges.html', context)


@login_required
@user_passes_test(is_staff)
def create_loan(request, pk):
    """Create loan from approved application (after charges added)"""
    staff_profile = request.user.staff_profile
    from datetime import date, timedelta

    application = get_object_or_404(LoanApplication, pk=pk)

    if application.status not in ['ready_for_disbursement', 'manager_approved', 'line_approved']:
        messages.error(request, 'Application must be approved before creating loan.')
        return redirect('staff:staff_applications')

    loan_product_name = application.loan_product.name if application.loan_product else 'APCP'
    is_trade_loan = loan_product_name.upper() == 'TRADE'

    if request.method == 'POST':
        loan_count = Loan.objects.count() + 1
        loan_number = f"LN-{date.today().year}-{loan_count:04d}"

        principal = float(application.approved_line if application.approved_line else application.requested_amount)
        interest_rate = float(application.loan_product.interest_rate) if application.loan_product else 15.0
        payment_type = request.POST.get('payment_type', 'flexible')

        if is_trade_loan:
            term_months = request.POST.get('term_months')
            if not term_months:
                messages.error(request, 'Please select a loan term for Trade loan.')
                return redirect('staff:create_loan', pk=pk)
            try:
                term_months = int(term_months)
            except ValueError:
                messages.error(request, 'Invalid loan term selected.')
                return redirect('staff:create_loan', pk=pk)
        else:
            term_months = int(request.POST.get('term_months', 12))

        monthly_rate = interest_rate / 100 / term_months

        if monthly_rate == 0:
            monthly_payment = principal / term_months
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / (
                        (1 + monthly_rate) ** term_months - 1)

        total_interest = (monthly_payment * term_months) - principal
        total_payable = principal + total_interest

        disbursement_date = date.today()
        term_days = term_months * 30
        due_date = date.today() + timedelta(days=term_days)
        next_due_date = date.today() + timedelta(days=30)

        loan = Loan.objects.create(
            loan_number=loan_number,
            application=application,
            borrower=application.member,
            loan_product=application.loan_product,
            principal_amount=principal,
            interest_rate=interest_rate,
            term_months=term_months,
            term_days=term_days,
            disbursement_date=disbursement_date,
            due_date=due_date,
            next_due_date=next_due_date,
            daily_interest_rate=interest_rate / 100 / 360,
            payment_type=payment_type,
            penalty_rate=0.02,
            penalty_start_days=361,
            remaining_balance=principal,
            monthly_payment=monthly_payment,
            total_interest=total_interest,
            total_payable_amount=total_payable,
            status='active',
            created_by=request.user,
            disbursed_by=request.user
        )

        application.status = 'disbursed'
        application.save()

        log_activity(staff_profile, 'CREATE', 'loan', loan.id, request)

        messages.success(request, f'Loan {loan_number} created and disbursed successfully!')
        return redirect('staff:loan_detail', pk=loan.id)

    context = {
        'staff_profile': staff_profile,
        'application': application,
        'principal': float(application.approved_line if application.approved_line else application.requested_amount),
        'interest_rate': float(application.loan_product.interest_rate) if application.loan_product else 15,
        'total_deductions': float(application.total_deductions) if application.total_deductions else 0,
        'net_proceeds': float(application.net_proceeds) if application.net_proceeds else float(
            application.approved_line if application.approved_line else application.requested_amount),
        'is_trade_loan': is_trade_loan,
        'loan_product_name': loan_product_name,
        'daily_rate': (float(application.loan_product.interest_rate) if application.loan_product else 15) / 100 / 360,
    }

    return render(request, 'staff/applications/create_loan.html', context)


@login_required
@user_passes_test(is_staff)
def create_application(request):
    """Create a new loan application"""
    staff_profile = request.user.staff_profile

    if request.method == 'POST':
        try:
            member_id = request.POST.get('member_id')
            loan_product_id = request.POST.get('loan_product_id')
            requested_amount = request.POST.get('requested_amount')
            purpose = request.POST.get('purpose')
            collateral = request.POST.get('collateral', '')
            payment_mode = request.POST.get('payment_mode', 'cash')
            notes = request.POST.get('notes', '')

            if not all([member_id, loan_product_id, requested_amount, purpose]):
                messages.error(request, 'Please fill in all required fields.')
                context = {
                    'staff_profile': staff_profile,
                    'loan_products': LoanProduct.objects.filter(is_active=True),
                    'members': Member.objects.filter(is_active=True)
                }
                return render(request, 'staff/applications/create.html', context)

            member = Member.objects.get(id=member_id)
            loan_product = LoanProduct.objects.get(id=loan_product_id)

            import random
            app_id = f"{loan_product.name[:4]}-{datetime.now().year}-{random.randint(1000, 9999)}"

            application = LoanApplication.objects.create(
                application_id=app_id,
                member=member,
                loan_product=loan_product,
                requested_amount=Decimal(requested_amount),
                purpose=purpose,
                collateral=collateral,
                payment_mode=payment_mode,
                notes=notes,
                status='pending_staff_review',
                date_applied=timezone.now().date(),
                applicant_user=request.user
            )

            if request.FILES.get('govt_id'):
                MemberDocument.objects.create(
                    member=member,
                    document_type='valid_id',
                    file=request.FILES['govt_id']
                )

            if request.FILES.get('proof_of_income'):
                MemberDocument.objects.create(
                    member=member,
                    document_type='proof_income',
                    file=request.FILES['proof_of_income']
                )

            if request.FILES.getlist('other_documents'):
                for doc in request.FILES.getlist('other_documents'):
                    MemberDocument.objects.create(
                        member=member,
                        document_type='others',
                        file=doc
                    )

            log_activity(staff_profile, 'CREATE', 'application', application.id, request)
            messages.success(request, f'Application {application.application_id} created successfully!')
            return redirect('staff:review_application', pk=application.id)

        except Member.DoesNotExist:
            messages.error(request, 'Selected member does not exist.')
        except LoanProduct.DoesNotExist:
            messages.error(request, 'Selected loan product does not exist.')
        except Exception as e:
            messages.error(request, f'Error creating application: {str(e)}')

        return redirect('staff:staff_applications')

    context = {
        'staff_profile': staff_profile,
        'loan_products': LoanProduct.objects.filter(is_active=True),
        'members': Member.objects.filter(is_active=True),
    }
    return render(request, 'staff/applications/create.html', context)


@login_required
@user_passes_test(is_staff)
def edit_application(request, pk):
    """Edit application"""
    staff_profile = request.user.staff_profile
    application = get_object_or_404(LoanApplication, pk=pk)

    if request.method == 'POST':
        application.loan_product_id = request.POST.get('loan_product_id', application.loan_product_id)
        application.requested_amount = request.POST.get('requested_amount', application.requested_amount)
        application.purpose = request.POST.get('purpose', application.purpose)
        application.collateral = request.POST.get('collateral', application.collateral)
        application.save()

        messages.success(request, f'Application {application.application_id} updated successfully!')
        return redirect('staff:staff_applications')

    loan_products = LoanProduct.objects.filter(is_active=True)

    context = {
        'staff_profile': staff_profile,
        'application': application,
        'loan_products': loan_products,
    }

    return render(request, 'staff/applications/edit.html', context)


# ==================== LOAN VIEWS ====================

@login_required
@user_passes_test(is_staff)
def loan_list(request):
    """Loan register - list all loans"""
    staff_profile = request.user.staff_profile

    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    loan_type = request.GET.get('loan_type', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    loans = Loan.objects.select_related('borrower', 'loan_product').all()

    if search:
        loans = loans.filter(
            Q(loan_number__icontains=search) |
            Q(borrower__first_name__icontains=search) |
            Q(borrower__last_name__icontains=search)
        )

    if status_filter != 'all':
        loans = loans.filter(status=status_filter)

    if loan_type != 'all':
        loans = loans.filter(loan_product__name=loan_type)

    if date_from:
        loans = loans.filter(disbursement_date__gte=date_from)
    if date_to:
        loans = loans.filter(disbursement_date__lte=date_to)

    from datetime import date
    today = date.today()
    for loan in loans:
        loan.loan_type = loan.loan_product.name if loan.loan_product else 'N/A'
        if loan.next_due_date and loan.next_due_date < today:
            loan.days_overdue = (today - loan.next_due_date).days
            if loan.days_overdue > 360:
                penalty_months = ((loan.days_overdue - 360) + 29) // 30
                loan.penalty_amount = float(loan.remaining_balance or 0) * 0.02 * penalty_months
            else:
                loan.penalty_amount = 0
        else:
            loan.days_overdue = 0
            loan.penalty_amount = 0

    active_loans_count = loans.filter(status='active').count()
    overdue_loans_count = loans.filter(status='overdue').count()
    restructured_loans_count = loans.filter(status='restructured').count()
    paid_loans_count = loans.filter(status='paid').count()
    total_loans = loans.count()
    total_principal = loans.aggregate(total=Sum('principal_amount'))['total'] or 0

    context = {
        'staff_profile': staff_profile,
        'loans': loans,
        'active_loans_count': active_loans_count,
        'overdue_loans_count': overdue_loans_count,
        'restructured_loans_count': restructured_loans_count,
        'paid_loans_count': paid_loans_count,
        'total_loans': total_loans,
        'total_principal': total_principal,
        'filter_params': request.GET.urlencode(),
    }

    return render(request, 'staff/loans/list.html', context)


@login_required
@user_passes_test(is_staff)
def loan_detail(request, pk):
    """Loan details with payment schedule"""
    staff_profile = request.user.staff_profile
    loan = get_object_or_404(Loan, pk=pk)

    context = {
        'staff_profile': staff_profile,
        'loan': loan,
    }

    return render(request, 'staff/loans/detail.html', context)


@login_required
@user_passes_test(is_staff)
def loan_payment_schedule(request, pk):
    """View loan payment schedule"""
    from datetime import date, timedelta
    loan = get_object_or_404(Loan, pk=pk)

    schedule = []
    balance = float(loan.remaining_balance)
    monthly_payment = float(loan.monthly_payment)
    interest_rate = float(loan.interest_rate)
    term_months = loan.term_months
    monthly_rate = interest_rate / 100 / term_months

    next_date = loan.next_due_date or (loan.disbursement_date + timedelta(days=30))

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
            'balance': round(max(0, balance), 2)
        })

        next_date = next_date + timedelta(days=30)
        if balance <= 0:
            break

    return JsonResponse({'schedule': schedule})


@login_required
@user_passes_test(is_staff)
def process_restructuring(request, pk):
    """Process loan restructuring"""
    loan = get_object_or_404(Loan, pk=pk)

    if request.method == 'POST':
        new_principal = request.POST.get('new_principal')
        new_term = request.POST.get('new_term', 12)
        reason = request.POST.get('reason')

        old_balance = float(loan.remaining_balance)
        penalty = float(loan.penalty_amount or 0)

        restructure = RestructuringRequest.objects.create(
            request_number=f"RST-{datetime.now().strftime('%Y%m%d')}-{RestructuringRequest.objects.count() + 1:04d}",
            member_id=loan.borrower.id,
            old_loan_id=loan.id,
            old_balance=old_balance,
            old_penalty=penalty,
            new_principal=new_principal,
            new_interest_rate=loan.interest_rate,
            new_term_months=new_term,
            reason=reason,
            status='pending_staff',
            staff_approved_by=request.user.staff_profile
        )

        messages.success(request, f'Restructuring request {restructure.request_number} created!')
        return redirect('staff:restructuring_list')

    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@user_passes_test(is_staff)
def export_loans(request):
    """Export loans to Excel"""
    from datetime import datetime
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Loan Register"

    headers = ['Loan #', 'Borrower', 'Loan Type', 'Principal', 'Interest Rate', 'Monthly Payment',
               'Remaining Balance', 'Status', 'Disbursement Date', 'Term (Months)']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='1e3c72', end_color='1e3c72', fill_type='solid')

    loans = Loan.objects.select_related('borrower', 'loan_product').all()
    for row, loan in enumerate(loans, 2):
        ws.cell(row=row, column=1, value=loan.loan_number)
        ws.cell(row=row, column=2, value=f"{loan.borrower.last_name}, {loan.borrower.first_name}")
        ws.cell(row=row, column=3, value=loan.loan_product.name if loan.loan_product else 'N/A')
        ws.cell(row=row, column=4, value=float(loan.principal_amount))
        ws.cell(row=row, column=5, value=float(loan.interest_rate))
        ws.cell(row=row, column=6, value=float(loan.monthly_payment))
        ws.cell(row=row, column=7, value=float(loan.remaining_balance))
        ws.cell(row=row, column=8, value=loan.status)
        ws.cell(row=row, column=9, value=loan.disbursement_date.strftime('%Y-%m-%d') if loan.disbursement_date else '')
        ws.cell(row=row, column=10, value=loan.term_months)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="loans_export_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    wb.save(response)

    return response


# ==================== PAYMENT VIEWS ====================

@login_required
@user_passes_test(is_staff)
def payment_list(request):
    """Payments page"""
    staff_profile = request.user.staff_profile

    context = {
        'staff_profile': staff_profile,
        'today_collection': 0,
        'week_collection': 0,
        'month_collection': 0,
        'pending_instructions': 0,
        'recent_payments': [],
    }

    return render(request, 'staff/payments/list.html', context)


@login_required
@user_passes_test(is_staff)
def payment_history(request):
    """Payment history page"""
    staff_profile = request.user.staff_profile
    payments = Payment.objects.filter(is_posted=True).order_by('-payment_date')[:50]

    context = {
        'staff_profile': staff_profile,
        'payments': payments,
    }

    return render(request, 'staff/payments/decision_history.html', context)


@login_required
@user_passes_test(is_staff)
def payment_detail(request, pk):
    """Payment detail page - also handles JSON requests"""
    staff_profile = request.user.staff_profile
    payment = get_object_or_404(Payment, pk=pk)

    # Check if it's an API request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'id': payment.id,
            'payment_number': payment.payment_number,
            'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
            'member_name': f"{payment.member.last_name}, {payment.member.first_name}" if payment.member else "Unknown",
            'member_id': payment.member.membership_number if payment.member else "N/A",
            'loan_number': payment.loan.loan_number if payment.loan else "N/A",
            'payment_method': payment.payment_method,
            'amount': float(payment.amount),
            'penalty_amount': float(payment.penalty_amount) if hasattr(payment, 'penalty_amount') else 0,
            'interest_amount': float(payment.interest_amount) if hasattr(payment, 'interest_amount') else 0,
            'principal_amount': float(payment.principal_amount) if hasattr(payment, 'principal_amount') else 0,
            'remaining_balance': float(payment.remaining_balance_after) if hasattr(payment,
                                                                                   'remaining_balance_after') else 0,
            'status': payment.status,
            'posted_by': payment.posted_by.get_full_name() if payment.posted_by else "Cashier",
        })

    # Regular HTML response for the detail page
    context = {
        'staff_profile': staff_profile,
        'payment': payment,
    }
    return render(request, 'staff/payments/detail.html', context)


@login_required
@user_passes_test(is_staff)
def issue_payment_instruction(request):
    """Issue payment instruction page"""
    staff_profile = request.user.staff_profile

    context = {
        'staff_profile': staff_profile,
    }

    return render(request, 'staff/payments/issue.html', context)


@csrf_exempt
@login_required
@user_passes_test(is_staff)
def issue_instruction_api(request):
    """API endpoint to issue payment instruction"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            instruction = PaymentInstruction.objects.create(
                instruction_number=f"PI-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                member_id=data.get('member_id'),
                loan_id=data.get('loan_id'),
                amount_to_collect=data.get('amount'),
                penalty_amount=data.get('penalty', 0),
                interest_amount=data.get('interest', 0),
                principal_amount=data.get('principal', 0),
                remaining_balance_after=data.get('remaining_balance', 0),
                next_due_date=datetime.now().date() + timedelta(days=30),
                issued_by=request.user.staff_profile
            )

            return JsonResponse({
                'success': True,
                'instruction_number': instruction.instruction_number,
                'amount': float(instruction.amount_to_collect),
                'penalty': float(instruction.penalty_amount),
                'interest': float(instruction.interest_amount),
                'principal': float(instruction.principal_amount),
                'remaining_balance': float(instruction.remaining_balance_after)
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@user_passes_test(is_staff)
def payment_receipt_json(request, pk):
    """Return payment receipt data as JSON"""
    from main.models import Payment

    payment = get_object_or_404(Payment, pk=pk)

    data = {
        'payment_number': payment.payment_number,
        'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
        'member_name': f"{payment.member.last_name}, {payment.member.first_name}" if payment.member else "Unknown",
        'member_id': payment.member.membership_number if payment.member else "N/A",
        'loan_number': payment.loan.loan_number if payment.loan else "N/A",
        'payment_method': payment.payment_method,
        'amount': float(payment.amount),
        'penalty_amount': 0,
        'interest_amount': 0,
        'principal_amount': float(payment.amount),
        'remaining_balance': float(payment.remaining_balance_after) if hasattr(payment,
                                                                               'remaining_balance_after') else 0,
        'status': payment.status,
        'posted_by': payment.posted_by.get_full_name() if payment.posted_by else "Cashier",
    }

    return JsonResponse(data)


# ==================== RESTRUCTURING VIEWS ====================

@login_required
@user_passes_test(is_staff)
def restructuring_list(request):
    """Restructuring Management page"""
    staff_profile = request.user.staff_profile

    pending_count = RestructuringRequest.objects.filter(
        status__in=['pending_staff', 'with_committee']
    ).count()
    approved_count = RestructuringRequest.objects.filter(
        status__in=['committee_approved', 'manager_approved']
    ).count()
    completed_count = RestructuringRequest.objects.filter(status='completed').count()
    total_requests = RestructuringRequest.objects.count()

    context = {
        'staff_profile': staff_profile,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'completed_count': completed_count,
        'total_requests': total_requests,
    }

    return render(request, 'staff/restructuring/list.html', context)


@login_required
@user_passes_test(is_staff)
def restructuring_detail(request, pk):
    """Restructuring detail page"""
    staff_profile = request.user.staff_profile
    restructure = get_object_or_404(RestructuringRequest, pk=pk)

    context = {
        'staff_profile': staff_profile,
        'restructure': restructure,
    }

    return render(request, 'staff/restructuring/detail.html', context)


@login_required
@user_passes_test(is_staff)
def restructuring_request_form(request, member_id=None):
    """Restructuring request form"""
    staff_profile = request.user.staff_profile

    context = {
        'staff_profile': staff_profile,
        'member_id': member_id,
    }

    return render(request, 'staff/restructuring/request.html', context)


# ==================== REPORT VIEWS ====================

@login_required
@user_passes_test(is_staff)
def reports_index(request):
    """Reports dashboard"""
    staff_profile = request.user.staff_profile

    context = {
        'staff_profile': staff_profile,
        'total_loans': Loan.objects.count(),
        'total_collection': 0,
        'total_members': Member.objects.count(),
        'overdue_loans': Loan.objects.filter(status='overdue').count(),
    }

    return render(request, 'staff/reports/index.html', context)


@login_required
@user_passes_test(is_staff)
def report_loan_summary(request):
    """API endpoint for loan summary report"""
    return JsonResponse({
        'loans': [
            {'type': 'APCP', 'count': 25, 'principal': 1250000, 'interest': 187500, 'total': 1437500, 'collection_rate': 95},
            {'type': 'NCL', 'count': 30, 'principal': 1500000, 'interest': 300000, 'total': 1800000, 'collection_rate': 88},
            {'type': 'SALARY', 'count': 15, 'principal': 750000, 'interest': 60000, 'total': 810000, 'collection_rate': 98},
        ],
        'total': {'count': 70, 'principal': 3500000, 'interest': 547500, 'total': 4047500, 'collection_rate': 92}
    })


@login_required
@user_passes_test(is_staff)
def report_collection(request):
    """API endpoint for collection report"""
    return JsonResponse({
        'daily': [
            {'date': '2026-05-01', 'count': 5, 'cash': 25000, 'quedan': 10000, 'pesada': 5000, 'total': 40000},
            {'date': '2026-05-02', 'count': 8, 'cash': 45000, 'quedan': 15000, 'pesada': 8000, 'total': 68000},
        ],
        'total': {'count': 13, 'cash': 70000, 'quedan': 25000, 'pesada': 13000, 'total': 108000}
    })


@login_required
@user_passes_test(is_staff)
def report_aging(request):
    """API endpoint for aging report"""
    return JsonResponse({
        'categories': [
            {'name': '0-30 days', 'count': 45, 'principal': 2250000, 'interest': 37500, 'penalty': 0, 'total': 2287500},
            {'name': '31-60 days', 'count': 8, 'principal': 400000, 'interest': 8000, 'penalty': 2000, 'total': 410000},
        ],
        'total': {'count': 53, 'principal': 2650000, 'interest': 45500, 'penalty': 2000, 'total': 2697500}
    })


@login_required
@user_passes_test(is_staff)
def report_member(request):
    """API endpoint for member report"""
    return JsonResponse({
        'types': [
            {'name': 'Regular Members', 'count': 150, 'loan_count': 80, 'borrowed': 4000000, 'paid': 3500000, 'remaining': 500000},
        ],
        'total': {'count': 150, 'loan_count': 80, 'borrowed': 4000000, 'paid': 3500000, 'remaining': 500000}
    })


@login_required
@user_passes_test(is_staff)
def report_loan_product(request):
    """API endpoint for loan product report"""
    return JsonResponse({
        'products': [
            {'name': 'APCP', 'interest_rate': 15, 'applications': 35, 'approved': 30, 'disbursed': 28, 'amount': 1400000, 'default_rate': 5},
            {'name': 'NCL', 'interest_rate': 20, 'applications': 40, 'approved': 35, 'disbursed': 32, 'amount': 1600000, 'default_rate': 8},
        ]
    })


@login_required
@user_passes_test(is_staff)
def report_restructuring(request):
    """API endpoint for restructuring report"""
    return JsonResponse({
        'requests': [
            {'number': 'RST-2026-001', 'member': 'Juan Dela Cruz', 'old_loan': 'LN-2025-001', 'old_balance': 30000,
             'restructure_amount': 35000, 'new_principal': 38000, 'status': 'approved', 'date': '2026-05-01'},
        ]
    })


@login_required
@user_passes_test(is_staff)
def report_penalty(request):
    """API endpoint for penalty report"""
    return JsonResponse({
        'penalties': [
            {'loan_number': 'LN-2025-001', 'member': 'Juan Dela Cruz', 'balance': 50000, 'days_overdue': 45, 'monthly_penalty': 1000, 'total_penalty': 1500},
        ],
        'total_penalty': 1500
    })


@login_required
@user_passes_test(is_staff)
def export_report_excel(request):
    """Export report to Excel"""
    from datetime import datetime
    report_type = request.GET.get('report_type', 'loan-summary')
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d")}.xlsx"'
    response.write(f"Report: {report_type}\nGenerated: {datetime.now()}")
    return response


@login_required
@user_passes_test(is_staff)
def export_report_pdf(request):
    """Export report to PDF"""
    from datetime import datetime
    report_type = request.GET.get('report_type', 'loan-summary')
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report_{datetime.now().strftime("%Y%m%d")}.pdf"'
    response.write(f"Report: {report_type}\nGenerated: {datetime.now()}")
    return response


# ==================== REPORT API ENDPOINTS ====================

@login_required
@user_passes_test(is_staff)
def report_loan_summary_api(request):
    """API endpoint for loan summary report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    # Parse date parameters
    start_date, end_date = parse_report_dates(period, date_param)

    # Get filtered loans
    loans = Loan.objects.filter(disbursement_date__gte=start_date, disbursement_date__lte=end_date)

    # Group by loan product type
    loan_types = ['APCP', 'NCL', 'SALARY', 'COLLATERAL', 'TRADE', 'B2B', 'PROVIDENTIAL']
    loan_data = []
    total_principal = 0
    total_interest = 0
    total_count = 0

    for loan_type in loan_types:
        type_loans = loans.filter(loan_product__loan_type=loan_type)
        count = type_loans.count()
        if count > 0 or loan_type == 'APCP':  # Show even if zero for consistency
            principal = type_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
            # Calculate total interest (simplified - can be enhanced)
            interest = principal * Decimal('0.15')
            total = principal + interest
            collection_rate = 100  # This should be calculated from actual payments

            loan_data.append({
                'type': loan_type,
                'count': count,
                'principal': float(principal),
                'interest': float(interest),
                'total': float(total),
                'collection_rate': collection_rate
            })
            total_principal += float(principal)
            total_interest += float(interest)
            total_count += count

    return JsonResponse({
        'loans': loan_data,
        'total': {
            'count': total_count,
            'principal': total_principal,
            'interest': total_interest,
            'total': total_principal + total_interest,
            'collection_rate': 100
        }
    })


@login_required
@user_passes_test(is_staff)
def report_collection_api(request):
    """API endpoint for collection report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    start_date, end_date = parse_report_dates(period, date_param)

    # Get filtered payments
    payments = Payment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status='completed'
    )

    # Group by date
    daily_data = {}
    date_range = end_date - start_date

    for i in range(date_range.days + 1):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        daily_data[date_str] = {'count': 0, 'cash': 0, 'quedan': 0, 'pesada': 0, 'total': 0}

    for payment in payments:
        date_str = payment.payment_date.strftime('%Y-%m-%d')
        method = payment.payment_method or 'cash'
        amount = float(payment.amount)

        if date_str in daily_data:
            daily_data[date_str]['count'] += 1
            daily_data[date_str]['total'] += amount
            if method == 'cash':
                daily_data[date_str]['cash'] += amount
            elif method == 'quedan':
                daily_data[date_str]['quedan'] += amount
            elif method == 'pesada':
                daily_data[date_str]['pesada'] += amount

    daily_list = [{'date': k, **v} for k, v in daily_data.items()]

    # Calculate totals
    total = {
        'count': sum(d['count'] for d in daily_list),
        'cash': sum(d['cash'] for d in daily_list),
        'quedan': sum(d['quedan'] for d in daily_list),
        'pesada': sum(d['pesada'] for d in daily_list),
        'total': sum(d['total'] for d in daily_list)
    }

    return JsonResponse({'daily': daily_list, 'total': total})


@login_required
@user_passes_test(is_staff)
def report_aging_api(request):
    """API endpoint for aging report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    start_date, end_date = parse_report_dates(period, date_param)
    today = date.today()

    # Get all active and overdue loans
    loans = Loan.objects.filter(Q(status='active') | Q(status='overdue'))

    # Categorize by days overdue
    aging_categories = [
        {'name': '0-30 days', 'min': 0, 'max': 30, 'count': 0, 'principal': 0, 'interest': 0, 'penalty': 0, 'total': 0},
        {'name': '31-60 days', 'min': 31, 'max': 60, 'count': 0, 'principal': 0, 'interest': 0, 'penalty': 0,
         'total': 0},
        {'name': '61-90 days', 'min': 61, 'max': 90, 'count': 0, 'principal': 0, 'interest': 0, 'penalty': 0,
         'total': 0},
        {'name': '91+ days', 'min': 91, 'max': 999, 'count': 0, 'principal': 0, 'interest': 0, 'penalty': 0,
         'total': 0},
        {'name': 'Not Overdue', 'min': -1, 'max': -1, 'count': 0, 'principal': 0, 'interest': 0, 'penalty': 0,
         'total': 0},
    ]

    for loan in loans:
        days_overdue = 0
        if loan.next_due_date and loan.next_due_date < today:
            days_overdue = (today - loan.next_due_date).days

        penalty = 0
        if days_overdue > 360:
            penalty_months = ((days_overdue - 360) + 29) // 30
            penalty = float(loan.remaining_balance or 0) * 0.02 * penalty_months

        principal = float(loan.remaining_balance or 0)
        interest = principal * 0.0125  # Approximate monthly interest
        total = principal + interest + penalty

        # Find appropriate category
        category_found = False
        for cat in aging_categories:
            if cat['name'] == 'Not Overdue' and days_overdue == 0:
                cat['count'] += 1
                cat['principal'] += principal
                cat['interest'] += interest
                cat['penalty'] += penalty
                cat['total'] += total
                category_found = True
                break
            elif cat['min'] <= days_overdue <= cat['max']:
                cat['count'] += 1
                cat['principal'] += principal
                cat['interest'] += interest
                cat['penalty'] += penalty
                cat['total'] += total
                category_found = True
                break

        if not category_found and days_overdue > 0:
            # If days_overdue > 90, add to the last category
            aging_categories[-1]['count'] += 1
            aging_categories[-1]['principal'] += principal
            aging_categories[-1]['interest'] += interest
            aging_categories[-1]['penalty'] += penalty
            aging_categories[-1]['total'] += total

    # Filter out empty categories for display
    categories = [cat for cat in aging_categories if cat['count'] > 0]

    total_data = {
        'count': sum(c['count'] for c in categories),
        'principal': sum(c['principal'] for c in categories),
        'interest': sum(c['interest'] for c in categories),
        'penalty': sum(c['penalty'] for c in categories),
        'total': sum(c['total'] for c in categories)
    }

    return JsonResponse({'categories': categories, 'total': total_data})


@login_required
@user_passes_test(is_staff)
def report_member_api(request):
    """API endpoint for member report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    start_date, end_date = parse_report_dates(period, date_param)

    # Get distinct members who took loans in the period
    loans = Loan.objects.filter(disbursement_date__gte=start_date, disbursement_date__lte=end_date)

    member_types = [
        {'name': 'Regular Members', 'count': 0, 'loan_count': 0, 'borrowed': 0, 'paid': 0, 'remaining': 0},
        {'name': 'Employee Members', 'count': 0, 'loan_count': 0, 'borrowed': 0, 'paid': 0, 'remaining': 0},
    ]

    # This is a simplified version - you should enhance with actual data
    all_members = Member.objects.filter(is_active=True)
    employee_members = all_members.filter(is_employee=True)
    regular_members = all_members.filter(is_employee=False)

    member_types[0]['count'] = regular_members.count()
    member_types[1]['count'] = employee_members.count()

    total_loans = Loan.objects.count()
    total_principal = Loan.objects.aggregate(total=Sum('principal_amount'))['total'] or 0
    total_paid = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0

    for mt in member_types:
        mt['loan_count'] = int(total_loans * (mt['count'] / max(all_members.count(), 1)))
        mt['borrowed'] = float(total_principal * (mt['count'] / max(all_members.count(), 1)))
        mt['paid'] = float(total_paid * (mt['count'] / max(all_members.count(), 1)))
        mt['remaining'] = mt['borrowed'] - mt['paid']

    total_data = {
        'count': all_members.count(),
        'loan_count': total_loans,
        'borrowed': float(total_principal),
        'paid': float(total_paid),
        'remaining': float(total_principal - total_paid)
    }

    return JsonResponse({'types': member_types, 'total': total_data})


@login_required
@user_passes_test(is_staff)
def report_loan_product_api(request):
    """API endpoint for loan product report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    start_date, end_date = parse_report_dates(period, date_param)

    products = LoanProduct.objects.filter(is_active=True)
    product_data = []

    for product in products:
        applications = LoanApplication.objects.filter(
            loan_product=product,
            date_applied__gte=start_date,
            date_applied__lte=end_date
        )
        approved = applications.filter(status__in=['manager_approved', 'ready_for_disbursement', 'disbursed'])
        disbursed = Loan.objects.filter(loan_product=product, disbursement_date__gte=start_date,
                                        disbursement_date__lte=end_date)

        total_amount = disbursed.aggregate(total=Sum('principal_amount'))['total'] or 0
        default_rate = 0  # Calculate based on actual defaults

        product_data.append({
            'name': product.display_name,
            'interest_rate': float(product.interest_rate),
            'applications': applications.count(),
            'approved': approved.count(),
            'disbursed': disbursed.count(),
            'amount': float(total_amount),
            'default_rate': default_rate
        })

    return JsonResponse({'products': product_data})


@login_required
@user_passes_test(is_staff)
def report_restructuring_api(request):
    """API endpoint for restructuring report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    start_date, end_date = parse_report_dates(period, date_param)

    restructures = RestructuringRequest.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )

    request_data = []
    for req in restructures:
        try:
            member = Member.objects.get(id=req.member_id)
            member_name = f"{member.last_name}, {member.first_name}"
        except:
            member_name = "Unknown"

        try:
            old_loan = Loan.objects.get(id=req.old_loan_id)
            old_loan_number = old_loan.loan_number
        except:
            old_loan_number = "N/A"

        request_data.append({
            'number': req.request_number,
            'member': member_name,
            'old_loan': old_loan_number,
            'old_balance': float(req.old_balance),
            'restructure_amount': float(req.new_charges),
            'new_principal': float(req.new_principal),
            'status': req.status,
            'date': req.created_at.strftime('%Y-%m-%d')
        })

    return JsonResponse({'requests': request_data})


@login_required
@user_passes_test(is_staff)
def report_penalty_api(request):
    """API endpoint for penalty report"""
    period = request.GET.get('period', 'monthly')
    date_param = request.GET.get('date', '')

    start_date, end_date = parse_report_dates(period, date_param)
    today = date.today()

    overdue_loans = Loan.objects.filter(status='overdue')

    penalties = []
    total_penalty = 0

    for loan in overdue_loans:
        days_overdue = 0
        if loan.next_due_date and loan.next_due_date < today:
            days_overdue = (today - loan.next_due_date).days

        if days_overdue > 360:
            penalty_months = ((days_overdue - 360) + 29) // 30
            penalty = float(loan.remaining_balance or 0) * 0.02 * penalty_months
            monthly_penalty = penalty / penalty_months if penalty_months > 0 else 0

            total_penalty += penalty

            penalties.append({
                'loan_number': loan.loan_number,
                'member': f"{loan.borrower.last_name}, {loan.borrower.first_name}",
                'balance': float(loan.remaining_balance or 0),
                'days_overdue': days_overdue,
                'monthly_penalty': monthly_penalty,
                'total_penalty': penalty
            })

    return JsonResponse({'penalties': penalties, 'total_penalty': total_penalty})


def parse_report_dates(period, date_param):
    """Helper function to parse report period and date parameters"""
    today = date.today()

    if period == 'daily':
        if date_param:
            start_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        else:
            start_date = today
        end_date = start_date

    elif period == 'weekly':
        if date_param and '|' in date_param:
            dates = date_param.split('|')
            start_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(dates[1], '%Y-%m-%d').date()
        else:
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

    elif period == 'monthly':
        if date_param:
            year, month = map(int, date_param.split('-'))
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            start_date = date(today.year, today.month, 1)
            if today.month == 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

    elif period == 'quarterly':
        if date_param and 'Q' in date_param:
            year, quarter = date_param.split('-Q')
            year = int(year)
            quarter = int(quarter)
            start_month = (quarter - 1) * 3 + 1
            start_date = date(year, start_month, 1)
            if start_month + 2 > 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, start_month + 3, 1) - timedelta(days=1)
        else:
            quarter = (today.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            start_date = date(today.year, start_month, 1)
            if start_month + 2 > 12:
                end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(today.year, start_month + 3, 1) - timedelta(days=1)

    elif period == 'yearly':
        if date_param:
            year = int(date_param)
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        else:
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)

    elif period == 'custom':
        if date_param and '|' in date_param:
            dates = date_param.split('|')
            start_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
            end_date = datetime.strptime(dates[1], '%Y-%m-%d').date()
        else:
            start_date = today - timedelta(days=30)
            end_date = today
    else:
        start_date = today - timedelta(days=30)
        end_date = today

    return start_date, end_date


# ==================== NOTIFICATION VIEWS ====================

@login_required
@user_passes_test(is_staff)
def notifications_page(request):
    """Notifications page"""
    staff_profile = request.user.staff_profile

    notifications = StaffNotification.objects.filter(staff=staff_profile).order_by('-created_at')
    total_notifications = notifications.count()
    unread_count = notifications.filter(is_read=False).count()
    read_count = total_notifications - unread_count
    system_notifications = notifications.filter(notification_type='system_alert').count()

    context = {
        'staff_profile': staff_profile,
        'notifications': notifications[:20],
        'total_notifications': total_notifications,
        'unread_count': unread_count,
        'read_count': read_count,
        'system_notifications': system_notifications,
    }

    return render(request, 'staff/notifications/list.html', context)


@login_required
@user_passes_test(is_staff)
def notifications_api(request):
    """API endpoint for notifications"""
    staff_profile = request.user.staff_profile
    unread_count = StaffNotification.objects.filter(staff=staff_profile, is_read=False).count()
    return JsonResponse({'unread_count': unread_count})


@login_required
@user_passes_test(is_staff)
def mark_notification_read(request, pk):
    """Mark a single notification as read"""
    if request.method == 'POST':
        try:
            notification = StaffNotification.objects.get(pk=pk, staff=request.user.staff_profile)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return JsonResponse({'success': True})
        except StaffNotification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@user_passes_test(is_staff)
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    if request.method == 'POST':
        StaffNotification.objects.filter(staff=request.user.staff_profile, is_read=False).update(is_read=True, read_at=timezone.now())
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid method'}, status=400)


# ==================== PROFILE VIEWS ====================

@login_required
@user_passes_test(is_staff)
def staff_profile_view(request):
    """Staff profile page"""
    staff_profile_obj = request.user.staff_profile

    applications_reviewed = StaffActivityLog.objects.filter(
        staff=staff_profile_obj, entity_type='application', action='REVIEW'
    ).count()
    loans_processed = StaffActivityLog.objects.filter(
        staff=staff_profile_obj, entity_type='loan', action='CREATE'
    ).count()
    payments_processed = StaffActivityLog.objects.filter(
        staff=staff_profile_obj, entity_type='payment', action='CREATE'
    ).count()
    recent_activities = StaffActivityLog.objects.filter(staff=staff_profile_obj).order_by('-created_at')[:10]

    context = {
        'staff_profile': staff_profile_obj,
        'applications_reviewed': applications_reviewed,
        'loans_processed': loans_processed,
        'payments_processed': payments_processed,
        'recent_activities': recent_activities,
    }

    return render(request, 'staff/profile/index.html', context)


@login_required
@user_passes_test(is_staff)
def edit_profile(request):
    """Edit profile page"""
    staff_profile = request.user.staff_profile

    context = {
        'staff_profile': staff_profile,
    }

    return render(request, 'staff/profile/edit.html', context)


@login_required
@user_passes_test(is_staff)
def update_profile(request):
    """Update staff profile"""
    if request.method == 'POST':
        staff_profile_obj = request.user.staff_profile
        user = request.user

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        staff_profile_obj.contact_number = request.POST.get('contact_number', staff_profile_obj.contact_number)
        staff_profile_obj.save()

        log_activity(staff_profile_obj, 'UPDATE', 'profile', staff_profile_obj.id, request)

        messages.success(request, 'Profile updated successfully!')
        return redirect('staff:staff_profile')

    return redirect('staff:staff_profile')


@login_required
@user_passes_test(is_staff)
def upload_avatar(request):
    """Upload profile picture"""
    if request.method == 'POST' and request.FILES.get('avatar'):
        staff_profile = request.user.staff_profile
        if staff_profile.profile_picture:
            import os
            if os.path.isfile(staff_profile.profile_picture.path):
                os.remove(staff_profile.profile_picture.path)
        staff_profile.profile_picture = request.FILES['avatar']
        staff_profile.save()
        messages.success(request, 'Profile picture updated successfully!')
    return redirect('staff:staff_profile')


@login_required
@user_passes_test(is_staff)
def change_password(request):
    """Change staff password"""
    if request.method == 'POST':
        user = request.user
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if not user.check_password(current):
            messages.error(request, 'Current password is incorrect.')
        elif new != confirm:
            messages.error(request, 'New passwords do not match.')
        elif len(new) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            user.set_password(new)
            user.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')

        return redirect('staff:staff_profile')

    return redirect('staff:staff_profile')


@login_required
@user_passes_test(is_staff)
def logout_all_devices(request):
    """Logout from all devices"""
    if request.method == 'POST':
        from django.contrib.auth import logout
        from django.contrib.sessions.models import Session

        user = request.user
        sessions = Session.objects.filter(
            session_key__in=[s.session_key for s in Session.objects.all()
                             if s.get_decoded().get('_auth_user_id') == str(user.id)]
        )
        sessions.delete()
        logout(request)

        messages.success(request, 'Logged out from all devices.')
        return redirect('main:login')

    return redirect('staff:staff_profile')


# ==================== API ENDPOINTS ====================

@login_required
@user_passes_test(is_staff)
def member_search(request):
    """Search members"""
    q = request.GET.get('q', '')
    members = Member.objects.filter(
        Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(membership_number__icontains=q)
    )[:10]

    results = [{'id': m.id, 'name': f"{m.last_name}, {m.first_name}", 'membership_id': m.membership_number,
                'contact': m.contact_number} for m in members]

    return JsonResponse({'member': results[0] if results else None, 'loans': []})


@login_required
@user_passes_test(is_staff)
def loan_status_api(request, loan_id):
    """Get loan status"""
    loan = get_object_or_404(Loan, pk=loan_id)

    return JsonResponse({
        'id': loan.id,
        'number': loan.loan_number,
        'remaining_balance': float(loan.remaining_balance),
        'next_due_date': loan.next_due_date.strftime('%Y-%m-%d') if loan.next_due_date else None,
        'monthly_payment': float(loan.monthly_payment),
        'status': loan.status,
    })


@login_required
@user_passes_test(is_staff)
def calculate_payment_breakdown(request):
    """Calculate payment breakdown"""
    amount = float(request.GET.get('amount', 0))
    balance = float(request.GET.get('balance', 0))

    interest = balance * 0.0166667
    principal = amount - interest if amount > interest else 0
    remaining = balance - principal if amount > interest else balance

    return JsonResponse({
        'penalty': 0,
        'interest': round(interest, 2),
        'principal': round(principal, 2),
        'remaining_balance': round(remaining, 2)
    })


@login_required
@user_passes_test(is_staff)
def application_api(request, pk):
    """API endpoint for application details"""
    try:
        app = get_object_or_404(LoanApplication, pk=pk)
        return JsonResponse({
            'id': app.id,
            'application_id': app.application_id,
            'member_name': f"{app.member.last_name}, {app.member.first_name}",
            'member_id': app.member.membership_number,
            'loan_product': app.loan_product.name if app.loan_product else 'N/A',
            'requested_amount': float(app.requested_amount),
            'approved_line': float(app.approved_line) if app.approved_line else 0,
            'net_proceeds': float(app.net_proceeds) if app.net_proceeds else 0,
            'purpose': app.purpose,
            'collateral': app.collateral,
            'status': app.status,
            'date_applied': app.date_applied.strftime('%Y-%m-%d'),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@user_passes_test(is_staff)
def bulk_forward(request):
    """Bulk forward applications to committee"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            app_ids = data.get('application_ids', [])
            updated = LoanApplication.objects.filter(id__in=app_ids, status='pending_staff_review').update(status='with_committee')
            return JsonResponse({'success': True, 'count': updated})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@user_passes_test(is_staff)
def bulk_reject(request):
    """Bulk reject applications"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            app_ids = data.get('application_ids', [])
            reason = data.get('reason', 'Bulk rejection')
            updated = LoanApplication.objects.filter(id__in=app_ids).update(status='rejected', staff_remarks=reason)
            return JsonResponse({'success': True, 'count': updated})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@user_passes_test(is_staff)
def validate_co_maker(request):
    """Validate co-maker by ID"""
    co_maker_id = request.GET.get('co_maker_id', '')

    try:
        co_maker = Member.objects.get(membership_number=co_maker_id, is_active=True)
        return JsonResponse({
            'valid': True,
            'name': f"{co_maker.last_name}, {co_maker.first_name}",
            'membership_id': co_maker.membership_number,
            'message': 'Co-maker validated successfully'
        })
    except Member.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Co-maker not found or inactive'
        })


# ==================== RESTRUCTURING API ====================

@csrf_exempt
@login_required
@user_passes_test(is_staff)
def restructuring_api_request(request):
    """API endpoint to submit a restructuring request"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            if not data.get('member_id'):
                return JsonResponse({'success': False, 'error': 'Member ID is required'})
            if not data.get('loan_id'):
                return JsonResponse({'success': False, 'error': 'Loan ID is required'})
            if not data.get('reason'):
                return JsonResponse({'success': False, 'error': 'Reason for restructuring is required'})

            calc = data.get('calculation', {})
            request_number = f"RST-{datetime.now().strftime('%Y%m%d')}-{str(datetime.now().timestamp())[-6:]}"

            restructuring = RestructuringRequest.objects.create(
                request_number=request_number,
                member_id=data.get('member_id'),
                old_loan_id=data.get('loan_id'),
                old_balance=calc.get('old_balance', 0),
                old_interest=calc.get('interest_due', 0),
                old_penalty=calc.get('penalty', 0),
                days_overdue=calc.get('days_overdue', 0),
                new_charges=calc.get('total_new_charges', 0),
                new_principal=calc.get('new_principal', 0),
                new_interest_rate=calc.get('interest_rate', 20),
                new_term_months=12,
                new_monthly_payment=calc.get('monthly_payment', 0),
                reason=data.get('reason', ''),
                status='pending_staff',
                staff_approved_by=request.user.staff_profile,
                staff_approved=True
            )

            return JsonResponse({
                'success': True,
                'request_number': request_number,
                'request_id': restructuring.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
@user_passes_test(is_staff)
def restructuring_api_list(request):
    """API endpoint to get list of restructuring requests"""
    requests = RestructuringRequest.objects.all().order_by('-created_at')[:50]

    result = []
    for req in requests:
        try:
            member = Member.objects.get(id=req.member_id)
            member_name = f"{member.last_name}, {member.first_name}"
        except:
            member_name = "Unknown"

        try:
            loan = Loan.objects.get(id=req.old_loan_id)
            loan_number = loan.loan_number
        except:
            loan_number = "N/A"

        status_map = {
            'pending_staff': ('Pending Staff', 'pending'),
            'with_committee': ('With Committee', 'committee'),
            'committee_approved': ('Committee Approved', 'approved'),
            'manager_approved': ('Manager Approved', 'approved'),
            'completed': ('Completed', 'completed'),
            'rejected': ('Rejected', 'rejected'),
        }
        status_display, status_class = status_map.get(req.status, (req.status, 'pending'))

        result.append({
            'id': req.id,
            'request_number': req.request_number,
            'member_name': member_name,
            'loan_number': loan_number,
            'old_balance': float(req.old_balance),
            'new_principal': float(req.new_principal),
            'new_monthly_payment': float(req.new_monthly_payment),
            'status': req.status,
            'status_display': status_display,
            'status_class': status_class,
            'created_at': req.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({'requests': result})


@login_required
@user_passes_test(is_staff)
def restructuring_api_detail(request, pk):
    """API endpoint to get details of a specific restructuring request"""
    restructure = get_object_or_404(RestructuringRequest, pk=pk)

    try:
        member = Member.objects.get(id=restructure.member_id)
        member_name = f"{member.last_name}, {member.first_name}"
        membership_number = member.membership_number
        contact = member.contact_number or 'N/A'
    except:
        member_name = "Unknown"
        membership_number = "N/A"
        contact = "N/A"

    try:
        loan = Loan.objects.get(id=restructure.old_loan_id)
        loan_number = loan.loan_number
        original_principal = float(loan.principal_amount)
    except:
        loan_number = "N/A"
        original_principal = 0

    status_map = {
        'pending_staff': ('Pending Staff', 'pending'),
        'with_committee': ('With Committee', 'committee'),
        'committee_approved': ('Committee Approved', 'approved'),
        'manager_approved': ('Manager Approved', 'approved'),
        'completed': ('Completed', 'completed'),
        'rejected': ('Rejected', 'rejected'),
    }
    status_display, status_class = status_map.get(restructure.status, (restructure.status, 'pending'))

    return JsonResponse({
        'id': restructure.id,
        'request_number': restructure.request_number,
        'member_name': member_name,
        'membership_number': membership_number,
        'contact': contact,
        'loan_number': loan_number,
        'original_principal': original_principal,
        'old_balance': float(restructure.old_balance),
        'old_interest': float(restructure.old_interest),
        'old_penalty': float(restructure.old_penalty),
        'new_principal': float(restructure.new_principal),
        'new_interest_rate': float(restructure.new_interest_rate),
        'new_monthly_payment': float(restructure.new_monthly_payment),
        'reason': restructure.reason,
        'status': restructure.status,
        'status_display': status_display,
        'status_class': status_class,
        'created_at': restructure.created_at.strftime('%Y-%m-%d %H:%M'),
        'completed_at': restructure.completed_at.strftime('%Y-%m-%d') if restructure.completed_at else None,
        'new_loan_id': restructure.new_loan_id,
    })


@login_required
@user_passes_test(is_staff)
def payment_receipt_api(request, pk):
    """API endpoint to get payment receipt details"""
    from main.models import Payment

    try:
        payment = get_object_or_404(Payment, pk=pk)

        # Get member name
        member_name = f"{payment.member.last_name}, {payment.member.first_name}" if payment.member else "Unknown"
        member_id = payment.member.membership_number if payment.member else "N/A"

        # Get loan number
        loan_number = payment.loan.loan_number if payment.loan else "N/A"

        # Get posted by name
        posted_by = payment.posted_by.get_full_name() if payment.posted_by else "Cashier"

        # Get payment details
        data = {
            'payment_number': payment.payment_number,
            'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
            'member_name': member_name,
            'member_id': member_id,
            'loan_number': loan_number,
            'payment_method': payment.payment_method if hasattr(payment, 'payment_method') else 'cash',
            'amount': float(payment.amount),
            'penalty_amount': float(payment.penalty_amount) if hasattr(payment, 'penalty_amount') else 0,
            'interest_amount': float(payment.interest_amount) if hasattr(payment, 'interest_amount') else 0,
            'principal_amount': float(payment.principal_amount) if hasattr(payment, 'principal_amount') else float(
                payment.amount),
            'remaining_balance': float(payment.remaining_balance_after) if hasattr(payment,
                                                                                   'remaining_balance_after') else 0,
            'posted_by': posted_by,
            'status': payment.status if hasattr(payment, 'status') else 'completed',
        }

        return JsonResponse(data)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)