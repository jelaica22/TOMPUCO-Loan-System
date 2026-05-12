# Add to staff/views.py
def overdue_accounts(request):
    """View and manage overdue accounts"""
    from datetime import date
    from main.models import Loan
    
    today = date.today()
    
    # Categorize overdue loans
    overdue_7_14 = Loan.objects.filter(
        due_date__lte=today,
        due_date__gt=today - timedelta(days=14),
        status='active',
        remaining_balance__gt=0
    )
    
    overdue_15_29 = Loan.objects.filter(
        due_date__lte=today - timedelta(days=15),
        due_date__gt=today - timedelta(days=30),
        status='active',
        remaining_balance__gt=0
    )
    
    overdue_30_plus = Loan.objects.filter(
        due_date__lte=today - timedelta(days=30),
        status='active',
        remaining_balance__gt=0
    )
    
    # Calculate penalties
    for loan in overdue_30_plus:
        days = (today - loan.due_date).days
        penalty_months = (days - 360) // 30 if days > 360 else 0
        if penalty_months > 0:
            loan.calculated_penalty = loan.remaining_balance * Decimal('0.02') * penalty_months
        else:
            loan.calculated_penalty = 0
    
    context = {
        'overdue_7_14': overdue_7_14,
        'overdue_15_29': overdue_15_29,
        'overdue_30_plus': overdue_30_plus,
        'total_overdue': overdue_7_14.count() + overdue_15_29.count() + overdue_30_plus.count(),
    }
    return render(request, 'staff/overdue_accounts.html', context)
