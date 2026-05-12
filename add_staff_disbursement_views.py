with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'def disbursement' not in content:
    new_views = '''

def disbursement(request):
    """Staff disbursement page - show approved applications"""
    from main.models import LoanApplication
    approved_apps = LoanApplication.objects.filter(status='manager_approved')
    return render(request, 'staff/disbursement.html', {'approved_applications': approved_apps})


def application_details(request, app_id):
    from django.http import JsonResponse
    from main.models import LoanApplication
    app = get_object_or_404(LoanApplication, id=app_id)
    # Calculate charges
    approved_line = float(app.approved_line)
    service_charge = approved_line * 0.03
    cbu = approved_line * 0.02
    insurance = approved_line * 0.0132
    total_charges = service_charge + cbu + insurance + 35 + 200
    
    return JsonResponse({
        'application_id': app.application_id,
        'member_name': f"{app.member.first_name} {app.member.last_name}",
        'loan_product': app.loan_product.name,
        'approved_line': str(app.approved_line),
        'total_charges': total_charges,
        'net_proceeds': float(app.approved_line) + total_charges,
    })


def disburse_loan(request, app_id):
    from django.http import JsonResponse
    from main.models import LoanApplication, Loan
    from decimal import Decimal
    import random
    from django.utils import timezone
    
    app = get_object_or_404(LoanApplication, id=app_id)
    
    if request.method == 'POST':
        try:
            # Calculate monthly payment
            principal = app.approved_line
            interest_rate = app.loan_product.interest_rate
            term_months = app.loan_product.term_months
            
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
            
            # Generate loan number
            year = timezone.now().year
            last_loan = Loan.objects.filter(loan_number__startswith=f'LN-{year}').order_by('-id').first()
            if last_loan:
                last_num = int(last_loan.loan_number.split('-')[-1])
                loan_number = f'LN-{year}-{str(last_num + 1).zfill(4)}'
            else:
                loan_number = f'LN-{year}-1000'
            
            # Create loan
            loan = Loan.objects.create(
                loan_number=loan_number,
                application=app,
                borrower=app.member,
                loan_product=app.loan_product,
                principal_amount=principal,
                remaining_balance=principal,
                interest_rate=interest_rate,
                term_months=term_months,
                monthly_payment=monthly_payment,
                disbursement_date=timezone.now().date(),
                status='active'
            )
            
            # Update application status
            app.status = 'active'
            app.save()
            
            return JsonResponse({'success': True, 'loan_number': loan_number})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})
'''
    content = content + new_views
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added disbursement views to staff')
