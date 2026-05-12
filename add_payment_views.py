import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add payment management functions
payment_functions = '''

@super_admin_required
def payments_list(request):
    from main.models import Payment, Loan
    from django.db.models import Q, Sum
    from datetime import datetime
    
    payments = Payment.objects.all().order_by('-payment_date')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    method = request.GET.get('method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search filter
    if search:
        payments = payments.filter(
            Q(payment_number__icontains=search) |
            Q(loan__loan_number__icontains=search) |
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search)
        )
    
    # Apply method filter
    if method and method != 'all':
        payments = payments.filter(payment_method=method)
    
    # Apply date filters
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__lte=date_to_parsed)
        except:
            pass
    
    active_loans = Loan.objects.filter(status='active')
    
    # Calculate stats
    total_payments = Payment.objects.count()
    cash_count = Payment.objects.filter(payment_method='cash').count()
    bank_count = Payment.objects.filter(payment_method='bank_transfer').count()
    check_count = Payment.objects.filter(payment_method='check').count()
    total_amount = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    return render(request, 'admin_panel/payments_list.html', {
        'payments': payments,
        'active_loans': active_loans,
        'total_payments': total_payments,
        'cash_count': cash_count,
        'bank_count': bank_count,
        'check_count': check_count,
        'total_amount': total_amount,
    })


@super_admin_required
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
    
    return redirect('admin_panel:payments_list')


@super_admin_required
def payment_detail(request, payment_id):
    from django.http import JsonResponse
    payment = get_object_or_404(Payment, id=payment_id)
    return JsonResponse({
        'id': payment.id,
        'payment_number': payment.payment_number,
        'loan_number': payment.loan.loan_number if payment.loan else '-',
        'borrower_name': f"{payment.member.first_name} {payment.member.last_name}" if payment.member else '-',
        'amount': str(payment.amount),
        'payment_date': payment.payment_date.strftime('%Y-%m-%d'),
        'payment_method': payment.payment_method,
        'payment_method_display': dict(Payment.PAYMENT_METHOD_CHOICES).get(payment.payment_method, payment.payment_method),
        'reference_number': payment.reference_number,
        'status': payment.status,
        'created_by': payment.created_by.username if hasattr(payment, 'created_by') and payment.created_by else 'System',
    })


@super_admin_required
def payment_edit(request, payment_id):
    from main.models import Payment
    from decimal import Decimal
    from django.utils import timezone
    
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
            
            # Adjust loan balance
            if payment.loan:
                amount_diff = new_amount - old_amount
                payment.loan.remaining_balance -= amount_diff
                if payment.loan.remaining_balance <= 0:
                    payment.loan.status = 'completed'
                    payment.loan.remaining_balance = 0
                payment.loan.save()
            
            messages.success(request, f'Payment {payment.payment_number} updated successfully')
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')
        return redirect('admin_panel:payments_list')
    
    return redirect('admin_panel:payments_list')


@super_admin_required
def payment_receipt(request, payment_id):
    from django.http import HttpResponse
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Draw receipt
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "TOMPuCO COOPERATIVE")
    p.setFont("Helvetica", 10)
    p.drawString(220, height - 70, "OFFICIAL PAYMENT RECEIPT")
    
    p.setFont("Helvetica", 10)
    y = height - 100
    p.drawString(50, y, f"Receipt #: {payment.payment_number}")
    p.drawString(50, y - 20, f"Date: {payment.payment_date.strftime('%Y-%m-%d')}")
    p.drawString(50, y - 40, f"Member: {payment.member.first_name} {payment.member.last_name}")
    p.drawString(50, y - 60, f"Loan #: {payment.loan.loan_number}")
    p.drawString(50, y - 80, f"Amount: ₱{payment.amount:,.2f}")
    p.drawString(50, y - 100, f"Payment Method: {payment.get_payment_method_display()}")
    if payment.reference_number:
        p.drawString(50, y - 120, f"Reference #: {payment.reference_number}")
    
    p.line(50, y - 130, width - 50, y - 130)
    p.setFont("Helvetica", 8)
    p.drawString(200, y - 150, "Thank you for your payment!")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


@super_admin_required
def payment_delete(request, payment_id):
    from django.http import JsonResponse
    payment = get_object_or_404(Payment, id=payment_id)
    if request.method == 'POST':
        payment_number = payment.payment_number
        payment.delete()
        return JsonResponse({'success': True, 'message': f'Payment {payment_number} deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})
'''

# Add the functions
content = content + payment_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added payment management functions')
