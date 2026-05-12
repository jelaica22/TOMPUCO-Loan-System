import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add payment schedule functions
schedule_functions = '''

@super_admin_required
def payment_schedules_list(request):
    from main.models import PaymentSchedule, Loan
    from django.db.models import Q
    from datetime import datetime
    
    schedules = PaymentSchedule.objects.all().order_by('due_date')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search filter
    if search:
        schedules = schedules.filter(
            Q(loan__loan_number__icontains=search) |
            Q(loan__borrower__first_name__icontains=search) |
            Q(loan__borrower__last_name__icontains=search)
        )
    
    # Apply status filter
    if status and status != 'all':
        schedules = schedules.filter(status=status)
    
    # Apply date filters
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            schedules = schedules.filter(due_date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            schedules = schedules.filter(due_date__lte=date_to_parsed)
        except:
            pass
    
    active_loans = Loan.objects.filter(status='active')
    
    # Calculate stats
    total_schedules = PaymentSchedule.objects.count()
    paid_count = PaymentSchedule.objects.filter(status='paid').count()
    pending_count = PaymentSchedule.objects.filter(status='pending').count()
    overdue_count = PaymentSchedule.objects.filter(status='overdue').count()
    
    return render(request, 'admin_panel/payment_schedules_list.html', {
        'schedules': schedules,
        'active_loans': active_loans,
        'total_schedules': total_schedules,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
    })


@super_admin_required
def payment_schedule_generate(request):
    from main.models import Loan, PaymentSchedule
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    if request.method == 'POST':
        try:
            loan_id = request.POST.get('loan_id')
            loan = get_object_or_404(Loan, id=loan_id)
            
            # Delete existing schedules for this loan
            PaymentSchedule.objects.filter(loan=loan).delete()
            
            # Generate 12 monthly schedules
            principal = loan.principal_amount
            interest_rate = loan.interest_rate
            term_months = loan.term_months
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
            
            remaining_balance = principal
            current_date = datetime.now().date()
            
            for month in range(1, term_months + 1):
                interest_due = remaining_balance * monthly_rate
                principal_due = monthly_payment - interest_due
                total_due = monthly_payment
                
                due_date = current_date + timedelta(days=30 * month)
                
                PaymentSchedule.objects.create(
                    loan=loan,
                    schedule_number=f"{loan.loan_number}-{month:02d}",
                    due_date=due_date,
                    principal_due=principal_due,
                    interest_due=interest_due,
                    total_due=total_due,
                    status='pending'
                )
                
                remaining_balance -= principal_due
            
            messages.success(request, f'Payment schedule generated for loan {loan.loan_number}')
        except Exception as e:
            messages.error(request, f'Error generating schedule: {str(e)}')
        return redirect('admin_panel:payment_schedules_list')
    
    return redirect('admin_panel:payment_schedules_list')


@super_admin_required
def payment_schedule_detail(request, schedule_id):
    from django.http import JsonResponse
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
        'paid_date': schedule.paid_date.strftime('%Y-%m-%d') if schedule.paid_date else None,
    })


@super_admin_required
def payment_schedule_edit(request, schedule_id):
    from decimal import Decimal
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    if request.method == 'POST':
        try:
            schedule.due_date = request.POST.get('due_date')
            schedule.principal_due = Decimal(request.POST.get('principal_due', 0))
            schedule.interest_due = Decimal(request.POST.get('interest_due', 0))
            schedule.total_due = schedule.principal_due + schedule.interest_due
            schedule.status = request.POST.get('status', schedule.status)
            schedule.save()
            messages.success(request, f'Schedule updated for loan {schedule.loan.loan_number}')
        except Exception as e:
            messages.error(request, f'Error updating schedule: {str(e)}')
        return redirect('admin_panel:payment_schedules_list')
    
    return redirect('admin_panel:payment_schedules_list')


@super_admin_required
def payment_schedule_mark_paid(request, schedule_id):
    from django.utils import timezone
    from django.http import JsonResponse
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    if request.method == 'POST':
        schedule.status = 'paid'
        schedule.paid_date = timezone.now().date()
        schedule.save()
        return JsonResponse({'success': True, 'message': 'Schedule marked as paid'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@super_admin_required
def payment_schedule_delete(request, schedule_id):
    from django.http import JsonResponse
    schedule = get_object_or_404(PaymentSchedule, id=schedule_id)
    if request.method == 'POST':
        schedule.delete()
        return JsonResponse({'success': True, 'message': 'Schedule deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})
'''

# Add the functions
content = content + schedule_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added payment schedule functions')
