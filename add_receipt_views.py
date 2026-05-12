import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add payment receipt functions
receipt_functions = '''

@super_admin_required
def payment_receipts_list(request):
    from main.models import PaymentReceipt
    from django.db.models import Q, Sum
    from datetime import datetime
    
    receipts = PaymentReceipt.objects.all().order_by('-generated_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    method = request.GET.get('method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search filter
    if search:
        receipts = receipts.filter(
            Q(receipt_number__icontains=search) |
            Q(payment__member__first_name__icontains=search) |
            Q(payment__member__last_name__icontains=search) |
            Q(payment__loan__loan_number__icontains=search)
        )
    
    # Apply method filter
    if method and method != 'all':
        receipts = receipts.filter(payment_method=method)
    
    # Apply date filters
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            receipts = receipts.filter(generated_at__date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            receipts = receipts.filter(generated_at__date__lte=date_to_parsed)
        except:
            pass
    
    # Calculate stats
    total_receipts = PaymentReceipt.objects.count()
    cash_count = PaymentReceipt.objects.filter(payment_method='cash').count()
    pesada_count = PaymentReceipt.objects.filter(payment_method='pesada').count()
    quedan_count = PaymentReceipt.objects.filter(payment_method='quedan').count()
    
    return render(request, 'admin_panel/payment_receipts_list.html', {
        'receipts': receipts,
        'total_receipts': total_receipts,
        'cash_count': cash_count,
        'pesada_count': pesada_count,
        'quedan_count': quedan_count,
    })


@super_admin_required
def payment_receipt_detail(request, receipt_id):
    from django.http import JsonResponse
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id)
    return JsonResponse({
        'id': receipt.id,
        'receipt_number': receipt.receipt_number,
        'member_name': f"{receipt.payment.member.first_name} {receipt.payment.member.last_name}",
        'loan_number': receipt.payment.loan.loan_number,
        'amount_paid': str(receipt.amount_paid),
        'payment_method': receipt.payment_method,
        'payment_method_display': dict(PaymentReceipt.PAYMENT_METHOD_CHOICES).get(receipt.payment_method, receipt.payment_method),
        'generated_at': receipt.generated_at.strftime('%Y-%m-%d %H:%M'),
        'generated_by': receipt.generated_by.username if receipt.generated_by else 'System',
        'pdf_url': receipt.receipt_pdf.url if receipt.receipt_pdf else None,
    })


@super_admin_required
def payment_receipt_delete(request, receipt_id):
    from django.http import JsonResponse
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id)
    if request.method == 'POST':
        receipt_number = receipt.receipt_number
        receipt.delete()
        return JsonResponse({'success': True, 'message': f'Receipt {receipt_number} deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@super_admin_required
def payment_receipt_report(request):
    from main.models import PaymentReceipt
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from io import BytesIO
    from datetime import datetime
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1e3c72'), alignment=TA_CENTER, spaceAfter=20)
    
    story = []
    story.append(Paragraph("PAYMENT RECEIPTS REPORT", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    receipts = PaymentReceipt.objects.all().order_by('-generated_at')
    
    data = [['Receipt #', 'Member', 'Loan #', 'Amount', 'Method', 'Date']]
    for r in receipts:
        data.append([
            r.receipt_number,
            f"{r.payment.member.first_name} {r.payment.member.last_name}",
            r.payment.loan.loan_number,
            f"₱{r.amount_paid:,.2f}",
            r.get_payment_method_display(),
            r.generated_at.strftime('%Y-%m-%d')
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')
'''

# Add the functions
content = content + receipt_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added payment receipt management functions')
