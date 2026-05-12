import sys
sys.path.insert(0, '.')

with open('manager/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add staff monitoring functions (view-only)
monitoring_views = '''

# ==================== STAFF MONITORING (VIEW ONLY) ====================

@login_required
@manager_required
def staff_applications(request):
    """View-only access to loan applications (monitoring staff work)"""
    from main.models import LoanApplication
    from django.db.models import Q
    from datetime import datetime
    
    applications = LoanApplication.objects.all().order_by('-created_at')
    
    # Apply filters if any
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    
    if search:
        applications = applications.filter(
            Q(application_id__icontains=search) |
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search)
        )
    if status and status != 'all':
        applications = applications.filter(status=status)
    
    # Statistics for staff performance monitoring
    total_applications = LoanApplication.objects.count()
    pending_count = LoanApplication.objects.filter(status='pending_staff_review').count()
    with_committee = LoanApplication.objects.filter(status='with_committee').count()
    approved_count = LoanApplication.objects.filter(status='manager_approved').count()
    rejected_count = LoanApplication.objects.filter(status='rejected').count()
    
    # Staff performance - time taken to process
    from datetime import timedelta
    avg_processing_time = None
    completed_apps = LoanApplication.objects.exclude(status='pending_staff_review').exclude(created_at__isnull=True)
    if completed_apps.exists():
        total_days = 0
        count = 0
        for app in completed_apps[:100]:
            if app.created_at and app.updated_at:
                delta = app.updated_at - app.created_at
                total_days += delta.days
                count += 1
        if count > 0:
            avg_processing_time = round(total_days / count, 1)
    
    return render(request, 'manager/staff_applications.html', {
        'applications': applications,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'with_committee': with_committee,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'avg_processing_time': avg_processing_time,
        'is_view_only': True,
    })


@login_required
@manager_required
def staff_loans(request):
    """View-only access to loans register"""
    from main.models import Loan
    
    loans = Loan.objects.all().order_by('-created_at')
    
    # Statistics
    total_loans = Loan.objects.count()
    active_loans = Loan.objects.filter(status='active').count()
    completed_loans = Loan.objects.filter(status='completed').count()
    overdue_loans = Loan.objects.filter(status='overdue').count()
    total_disbursed = Loan.objects.aggregate(total=models.Sum('principal_amount'))['total'] or 0
    
    return render(request, 'manager/staff_loans.html', {
        'loans': loans,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'overdue_loans': overdue_loans,
        'total_disbursed': total_disbursed,
        'is_view_only': True,
    })


@login_required
@manager_required
def staff_payments(request):
    """View-only access to payments"""
    from main.models import Payment
    
    payments = Payment.objects.all().order_by('-payment_date')
    
    # Statistics
    total_payments = Payment.objects.count()
    total_amount = Payment.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    cash_payments = Payment.objects.filter(payment_method='cash').count()
    pesada_payments = Payment.objects.filter(payment_method='pesada').count()
    quedan_payments = Payment.objects.filter(payment_method='quedan').count()
    
    return render(request, 'manager/staff_payments.html', {
        'payments': payments,
        'total_payments': total_payments,
        'total_amount': total_amount,
        'cash_count': cash_payments,
        'pesada_count': pesada_payments,
        'quedan_count': quedan_payments,
        'is_view_only': True,
    })


@login_required
@manager_required
def payment_instructions(request):
    """View-only access to payment instructions issued by staff"""
    from main.models import PaymentInstruction
    
    instructions = PaymentInstruction.objects.all().order_by('-created_at')
    
    pending_count = instructions.filter(status='pending').count()
    completed_count = instructions.filter(status='completed').count()
    
    return render(request, 'manager/payment_instructions.html', {
        'instructions': instructions,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'is_view_only': True,
    })


@login_required
@manager_required
def restructuring_requests(request):
    """View-only access to restructuring requests"""
    from main.models import RestructuringRequest
    
    requests = RestructuringRequest.objects.all().order_by('-created_at')
    
    pending = requests.filter(status='pending').count()
    approved = requests.filter(status='approved').count()
    rejected = requests.filter(status='rejected').count()
    
    return render(request, 'manager/restructuring_requests.html', {
        'requests': requests,
        'pending_count': pending,
        'approved_count': approved,
        'rejected_count': rejected,
        'is_view_only': True,
    })
'''

# Append to views.py
content = content + monitoring_views

with open('manager/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added staff monitoring views to manager portal')
