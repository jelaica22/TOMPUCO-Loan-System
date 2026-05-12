import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add loan management functions
loan_functions = '''

@super_admin_required
def loans_list(request):
    from django.db.models import Q, Sum
    from main.models import Loan, Member, LoanProduct
    
    loans = Loan.objects.all().order_by('-created_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    member_id = request.GET.get('member_id', '')
    
    # Apply search filter
    if search:
        loans = loans.filter(
            Q(loan_number__icontains=search) |
            Q(borrower__first_name__icontains=search) |
            Q(borrower__last_name__icontains=search)
        )
    
    # Apply status filter
    if status and status != 'all':
        loans = loans.filter(status=status)
    
    # Apply member filter
    if member_id and member_id != 'all':
        loans = loans.filter(borrower_id=member_id)
    
    all_members = Member.objects.filter(is_active=True)
    loan_products = LoanProduct.objects.filter(is_active=True)
    
    # Calculate stats
    total_loans = Loan.objects.count()
    active_count = Loan.objects.filter(status='active').count()
    completed_count = Loan.objects.filter(status='completed').count()
    overdue_count = Loan.objects.filter(status='overdue').count()
    total_amount = Loan.objects.aggregate(total=Sum('principal_amount'))['total'] or 0
    
    return render(request, 'admin_panel/loans_list.html', {
        'loans': loans,
        'all_members': all_members,
        'loan_products': loan_products,
        'total_loans': total_loans,
        'active_count': active_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'total_amount': total_amount,
    })


@super_admin_required
def loan_create(request):
    from main.models import Loan, Member, LoanApplication, PaymentSchedule
    from decimal import Decimal
    import random
    
    if request.method == 'POST':
        try:
            borrower_id = request.POST.get('borrower_id')
            product_id = request.POST.get('product_id')
            principal_amount = Decimal(request.POST.get('principal_amount', 0))
            interest_rate = Decimal(request.POST.get('interest_rate', 0))
            term_months = int(request.POST.get('term_months', 12))
            disbursement_date = request.POST.get('disbursement_date')
            status = request.POST.get('status', 'active')
            
            borrower = get_object_or_404(Member, id=borrower_id)
            product = get_object_or_404(LoanProduct, id=product_id)
            
            # Generate loan number
            year = timezone.now().year
            last_loan = Loan.objects.filter(loan_number__startswith=f'LN-{year}').order_by('-id').first()
            if last_loan:
                last_num = int(last_loan.loan_number.split('-')[-1])
                loan_number = f'LN-{year}-{str(last_num + 1).zfill(4)}'
            else:
                loan_number = f'LN-{year}-1000'
            
            # Calculate monthly payment using diminishing method
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = principal_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
            
            # Create loan
            loan = Loan.objects.create(
                loan_number=loan_number,
                borrower=borrower,
                loan_product=product,
                principal_amount=principal_amount,
                remaining_balance=principal_amount,
                interest_rate=interest_rate,
                term_months=term_months,
                term_days=term_months * 30,
                monthly_payment=monthly_payment,
                disbursement_date=disbursement_date,
                due_date=disbursement_date,
                status=status
            )
            
            messages.success(request, f'Loan {loan_number} created successfully for {borrower.first_name} {borrower.last_name}')
        except Exception as e:
            messages.error(request, f'Error creating loan: {str(e)}')
        return redirect('admin_panel:loans_list')
    
    return redirect('admin_panel:loans_list')


@super_admin_required
def loan_detail(request, loan_id):
    from django.http import JsonResponse
    from main.models import Loan
    loan = get_object_or_404(Loan, id=loan_id)
    return JsonResponse({
        'id': loan.id,
        'loan_number': loan.loan_number,
        'borrower_name': f"{loan.borrower.first_name} {loan.borrower.last_name}",
        'principal_amount': str(loan.principal_amount),
        'remaining_balance': str(loan.remaining_balance),
        'interest_rate': str(loan.interest_rate),
        'monthly_payment': str(loan.monthly_payment) if hasattr(loan, 'monthly_payment') else '0',
        'disbursement_date': loan.disbursement_date.strftime('%Y-%m-%d') if loan.disbursement_date else None,
        'due_date': loan.due_date.strftime('%Y-%m-%d') if loan.due_date else None,
        'status': loan.status,
        'notes': getattr(loan, 'notes', ''),
        'created_at': loan.created_at.strftime('%Y-%m-%d %H:%M') if loan.created_at else None,
    })


@super_admin_required
def loan_edit(request, loan_id):
    from main.models import Loan
    from decimal import Decimal
    
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        try:
            loan.principal_amount = Decimal(request.POST.get('principal_amount', loan.principal_amount))
            loan.interest_rate = Decimal(request.POST.get('interest_rate', loan.interest_rate))
            loan.remaining_balance = Decimal(request.POST.get('remaining_balance', loan.remaining_balance))
            loan.status = request.POST.get('status', loan.status)
            loan.notes = request.POST.get('notes', '')
            loan.save()
            messages.success(request, f'Loan {loan.loan_number} updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating loan: {str(e)}')
        return redirect('admin_panel:loans_list')
    
    return redirect('admin_panel:loans_list')


@super_admin_required
def loan_payment(request, loan_id):
    from main.models import Loan, Payment, PaymentSchedule
    from decimal import Decimal
    from django.utils import timezone
    
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount', 0))
            payment_method = request.POST.get('payment_method', 'cash')
            reference_number = request.POST.get('reference_number', '')
            
            # Generate payment number
            year = timezone.now().year
            last_payment = Payment.objects.filter(payment_number__startswith=f'PAY-{year}').order_by('-id').first()
            if last_payment:
                last_num = int(last_payment.payment_number.split('-')[-1])
                payment_number = f'PAY-{year}-{str(last_num + 1).zfill(6)}'
            else:
                payment_number = f'PAY-{year}-000001'
            
            # Create payment
            payment = Payment.objects.create(
                payment_number=payment_number,
                loan=loan,
                member=loan.borrower,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference_number,
                status='completed'
            )
            
            # Update loan balance
            loan.remaining_balance -= amount
            if loan.remaining_balance <= 0:
                loan.status = 'completed'
                loan.remaining_balance = 0
            loan.save()
            
            messages.success(request, f'Payment of ₱{amount:,.2f} recorded for loan {loan.loan_number}')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
        return redirect('admin_panel:loans_list')
    
    return redirect('admin_panel:loans_list')


@super_admin_required
def loan_delete(request, loan_id):
    from django.http import JsonResponse
    from main.models import Loan
    loan = get_object_or_404(Loan, id=loan_id)
    if request.method == 'POST':
        loan_number = loan.loan_number
        loan.delete()
        return JsonResponse({'success': True, 'message': f'Loan {loan_number} deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})
'''

# Add the functions to the views file
content = content + loan_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added loan management functions')
