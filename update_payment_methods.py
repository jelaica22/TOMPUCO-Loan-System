import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update payment method choices in payment_create function
old_payment_create = '''@super_admin_required
def payment_create(request):
    from main.models import Payment, Loan
    from decimal import Decimal
    from django.utils import timezone
    import random
    
    if request.method == 'POST':
        try:
            loan_id = request.POST.get('loan_id')
            amount = Decimal(request.POST.get('amount', 0))
            payment_date = request.POST.get('payment_date', timezone.now().date())
            payment_method = request.POST.get('payment_method', 'cash')
            reference_number = request.POST.get('reference_number', '')
            
            loan = get_object_or_404(Loan, id=loan_id)
            
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
                payment_date=payment_date,
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
            
            messages.success(request, f'Payment {payment_number} recorded successfully for {loan.loan_number}')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
        return redirect('admin_panel:payments_list')
    
    return redirect('admin_panel:payments_list')'''

new_payment_create = '''@super_admin_required
def payment_create(request):
    from main.models import Payment, Loan
    from decimal import Decimal
    from django.utils import timezone
    import random
    
    if request.method == 'POST':
        try:
            loan_id = request.POST.get('loan_id')
            amount = Decimal(request.POST.get('amount', 0))
            payment_date = request.POST.get('payment_date', timezone.now().date())
            payment_method = request.POST.get('payment_method', 'cash')
            reference_number = request.POST.get('reference_number', '')
            
            loan = get_object_or_404(Loan, id=loan_id)
            
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
                payment_date=payment_date,
                payment_method=payment_method,
                reference_number=reference_number if payment_method != 'cash' else '',
                status='completed'
            )
            
            # Update loan balance
            loan.remaining_balance -= amount
            if loan.remaining_balance <= 0:
                loan.status = 'completed'
                loan.remaining_balance = 0
            loan.save()
            
            messages.success(request, f'Payment {payment_number} recorded successfully for {loan.loan_number}')
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
        return redirect('admin_panel:payments_list')
    
    return redirect('admin_panel:payments_list')'''

content = content.replace(old_payment_create, new_payment_create)

# Also update the template to have correct payment methods
with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    pass  # Just to keep the script running

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated payment_create function with correct payment methods')
