with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add application review views
review_views = '''

@login_required
@staff_required
def review_application(request, app_id):
    """Review loan application"""
    app = get_object_or_404(LoanApplication, id=app_id)
    return render(request, 'staff/review_application.html', {'app': app})


@login_required
@staff_required
def add_charges(request, app_id):
    """Add charges to approved line"""
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        service_charge = Decimal(request.POST.get('service_charge', 0))
        cbu_retention = Decimal(request.POST.get('cbu_retention', 0))
        insurance_charge = Decimal(request.POST.get('insurance_charge', 0))
        service_fee = Decimal(request.POST.get('service_fee', 0))
        notarial_fee = Decimal(request.POST.get('notarial_fee', 0))
        inspector_fee = Decimal(request.POST.get('inspector_fee', 0))
        
        total_deductions = service_charge + cbu_retention + insurance_charge + service_fee + notarial_fee + inspector_fee
        net_proceeds = app.approved_line - total_deductions
        
        app.service_charge = service_charge
        app.cbu_retention = cbu_retention
        app.insurance_charge = insurance_charge
        app.service_fee = service_fee
        app.notarial_fee = notarial_fee
        app.inspector_fee = inspector_fee
        app.total_deductions = total_deductions
        app.net_proceeds = net_proceeds
        app.status = 'pending_manager_approval'
        app.save()
        
        messages.success(request, 'Charges added and forwarded to manager for approval.')
        return redirect('staff:staff_applications')
    
    return render(request, 'staff/add_charges.html', {'app': app})


@login_required
@staff_required
def create_loan(request, app_id):
    """Create loan from approved application"""
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        try:
            principal = app.approved_line
            interest_rate = app.interest_rate or app.loan_product.interest_rate
            term_months = app.loan_product.term_months
            
            monthly_rate = interest_rate / 100 / 12
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
            
            year = timezone.now().year
            last_loan = Loan.objects.filter(loan_number__startswith=f'LN-{year}').order_by('-id').first()
            if last_loan:
                last_num = int(last_loan.loan_number.split('-')[-1])
                loan_number = f'LN-{year}-{str(last_num + 1).zfill(4)}'
            else:
                loan_number = f'LN-{year}-1000'
            
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
            
            # Generate payment schedule
            from datetime import timedelta
            remaining = principal
            due_date = timezone.now().date() + timedelta(days=30)
            
            for month in range(1, term_months + 1):
                interest_due = remaining * monthly_rate
                principal_due = monthly_payment - interest_due
                PaymentSchedule.objects.create(
                    loan=loan,
                    schedule_number=f"{loan_number}-{month:02d}",
                    due_date=due_date,
                    principal_due=principal_due,
                    interest_due=interest_due,
                    total_due=monthly_payment,
                    status='pending'
                )
                remaining -= principal_due
                due_date += timedelta(days=30)
            
            app.status = 'active'
            app.save()
            
            messages.success(request, f'Loan {loan_number} created successfully!')
            return redirect('staff:staff_loans')
        except Exception as e:
            messages.error(request, f'Error creating loan: {str(e)}')
    
    return render(request, 'staff/create_loan.html', {'app': app})
'''

if 'def review_application' not in content:
    content = content + review_views
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added application review views')
