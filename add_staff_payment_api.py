import sys
sys.path.insert(0, '.')

with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

api_functions = '''

def api_search_loan(request):
    from main.models import Loan, Member
    q = request.GET.get('q', '')
    loan = None
    if q.startswith('LN-'):
        loan = Loan.objects.filter(loan_number=q, status='active').first()
    else:
        member = Member.objects.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(membership_number__icontains=q)
        ).first()
        if member:
            loan = Loan.objects.filter(borrower=member, status='active').first()
    if loan:
        return JsonResponse({'success': True, 'loan_id': loan.id})
    return JsonResponse({'success': False, 'error': 'No active loan found'})


def api_loan_details(request, loan_id):
    from main.models import Loan
    from datetime import date
    loan = get_object_or_404(Loan, id=loan_id)
    days_overdue = 0
    penalty = 0
    if loan.due_date and loan.due_date < date.today():
        days_overdue = (date.today() - loan.due_date).days
        if days_overdue > 360:
            penalty_months = (days_overdue - 360 + 29) // 30
            penalty = loan.remaining_balance * Decimal('0.02') * penalty_months
    return JsonResponse({
        'id': loan.id, 'loan_number': loan.loan_number,
        'member_name': f"{loan.borrower.first_name} {loan.borrower.last_name}",
        'principal': str(loan.principal_amount), 'balance': str(loan.remaining_balance),
        'monthly_payment': str(loan.monthly_payment),
        'due_date': loan.due_date.strftime('%Y-%m-%d') if loan.due_date else 'N/A',
        'days_overdue': days_overdue, 'penalty': float(penalty),
    })


def api_issue_payment_instruction(request):
    from main.models import Loan, PaymentInstruction
    import random
    if request.method == 'POST':
        data = json.loads(request.body)
        loan = get_object_or_404(Loan, id=data.get('loan_id'))
        amount = Decimal(data.get('amount'))
        instruction_number = f"PI-{timezone.now().year}-{random.randint(10000,99999)}"
        instruction = PaymentInstruction.objects.create(
            instruction_number=instruction_number, loan=loan, amount=amount,
            status='pending', issued_by=request.user
        )
        Notification.objects.create(user=loan.borrower.user, title='Payment Instruction Issued',
            message=f'A payment instruction for ₱{amount:,.2f} has been issued for loan {loan.loan_number}.',
            notification_type='payment_instruction')
        return JsonResponse({'success': True, 'instruction_number': instruction_number})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def api_payment_detail(request, payment_id):
    from main.models import Payment
    payment = get_object_or_404(Payment, id=payment_id)
    return JsonResponse({
        'payment_number': payment.payment_number,
        'member_name': f"{payment.member.first_name} {payment.member.last_name}",
        'loan_number': payment.loan.loan_number, 'amount': str(payment.amount),
        'payment_method': payment.get_payment_method_display(), 'date': payment.payment_date.strftime('%Y-%m-%d'),
        'status': payment.status, 'posted_by': payment.posted_by.username if payment.posted_by else 'Cashier',
    })


def api_payment_receipt(request, payment_id):
    from main.models import Payment
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from io import BytesIO
    payment = get_object_or_404(Payment, id=payment_id)
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1e3c72'), alignment=1)
    story = [Paragraph("TOMPuCO COOPERATIVE", title_style), Paragraph("OFFICIAL PAYMENT RECEIPT", styles['Normal']), Spacer(1, 20)]
    data = [['Receipt #:', payment.payment_number], ['Date:', payment.payment_date.strftime('%Y-%m-%d')],
            ['Member:', f"{payment.member.first_name} {payment.member.last_name}"],
            ['Loan #:', payment.loan.loan_number], ['Amount:', f"₱{payment.amount:,.2f}"],
            ['Payment Method:', payment.get_payment_method_display()]]
    table = Table(data, colWidths=[100, 300])
    table.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
'''

if 'def api_search_loan' not in content:
    content = content.replace('from django.http import JsonResponse', 'from django.http import JsonResponse\nimport json')
    content = content + api_functions
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added payment API endpoints to staff views')
