import sys
sys.path.insert(0, '.')

with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the issue_payment_instruction function and enhance it
payment_instruction_func = '''

def issue_payment_instruction(request, loan_id=None):
    """Issue payment instruction for a loan"""
    from main.models import Loan, PaymentInstruction, Notification
    
    if loan_id:
        loan = get_object_or_404(Loan, id=loan_id)
    else:
        loan_id = request.GET.get('loan_id')
        loan = get_object_or_404(Loan, id=loan_id) if loan_id else None
    
    if request.method == 'POST':
        loan = get_object_or_404(Loan, id=request.POST.get('loan_id'))
        amount_due = Decimal(request.POST.get('amount_due', 0))
        due_date = request.POST.get('due_date')
        
        # Create payment instruction
        instruction = PaymentInstruction.objects.create(
            loan=loan,
            amount_due=amount_due,
            due_date=due_date,
            issued_by=request.user,
            status='pending'
        )
        
        # Notify member
        Notification.objects.create(
            user=loan.borrower.user,
            title='Payment Instruction Issued',
            message=f'A payment instruction for ₱{amount_due:,.2f} has been issued for loan {loan.loan_number}. Please proceed to the cashier.',
            notification_type='payment_instruction',
            link='/payments/'
        )
        
        messages.success(request, f'Payment instruction issued for loan {loan.loan_number}')
        return redirect('staff:payment_instructions')
    
    # Get upcoming due loans
    from datetime import date, timedelta
    upcoming_loans = Loan.objects.filter(
        status='active',
        due_date__lte=date.today() + timedelta(days=15),
        remaining_balance__gt=0
    ).select_related('borrower')
    
    context = {
        'loans': upcoming_loans,
        'selected_loan': loan,
    }
    return render(request, 'staff/issue_payment_instruction.html', context)
'''

# Add if not exists
if 'def issue_payment_instruction' not in content:
    content = content + payment_instruction_func
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Enhanced payment instruction issuance')
