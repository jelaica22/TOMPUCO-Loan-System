import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Enhanced full receipt function with all details
enhanced_receipt_func = '''

@super_admin_required
def payment_receipt(request, payment_id):
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from io import BytesIO
    from datetime import datetime
    
    payment = get_object_or_404(Payment, id=payment_id)
    loan = payment.loan
    borrower = loan.borrower
    
    # Get payment schedule info
    try:
        next_schedule = loan.payment_schedules.filter(status='pending').order_by('due_date').first()
        next_due_date = next_schedule.due_date if next_schedule else None
        next_due_amount = next_schedule.total_due if next_schedule else 0
    except:
        next_due_date = None
        next_due_amount = 0
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#1e3c72'), alignment=TA_CENTER, spaceAfter=6)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#6c757d'), alignment=TA_CENTER, spaceAfter=20)
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#1e3c72'), fontName='Helvetica-Bold')
    label_style = ParagraphStyle('LabelStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6c757d'), fontName='Helvetica-Bold')
    value_style = ParagraphStyle('ValueStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#2c3e50'), fontName='Helvetica')
    amount_style = ParagraphStyle('AmountStyle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#1e3c72'), fontName='Helvetica-Bold')
    
    story = []
    
    # Header
    story.append(Paragraph("TOMPuCO COOPERATIVE", title_style))
    story.append(Paragraph("OFFICIAL PAYMENT RECEIPT", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1e3c72'), spaceBefore=5, spaceAfter=10))
    
    # Receipt Info
    receipt_data = [
        [Paragraph("<b>Receipt Number:</b>", label_style), Paragraph(f"{payment.payment_number}", value_style),
         Paragraph("<b>Transaction Date:</b>", label_style), Paragraph(f"{payment.payment_date.strftime('%B %d, %Y at %I:%M %p')}", value_style)],
        [Paragraph("<b>Status:</b>", label_style), Paragraph("<font color='green'><b>COMPLETED</b></font>", value_style),
         Paragraph("<b>Processed By:</b>", label_style), Paragraph(f"{request.user.get_full_name() or request.user.username}", value_style)],
    ]
    receipt_table = Table(receipt_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.8*inch])
    receipt_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(receipt_table)
    story.append(Spacer(1, 10))
    
    # Member Information
    story.append(Paragraph("MEMBER INFORMATION", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    member_data = [
        [Paragraph("<b>Member Name:</b>", label_style), Paragraph(f"{borrower.first_name} {borrower.last_name}", value_style),
         Paragraph("<b>Membership #:</b>", label_style), Paragraph(f"{borrower.membership_number or 'N/A'}", value_style)],
        [Paragraph("<b>Contact Number:</b>", label_style), Paragraph(f"{borrower.contact_number or 'N/A'}", value_style),
         Paragraph("<b>Address:</b>", label_style), Paragraph(f"{borrower.residence_address or 'N/A'}", value_style)],
    ]
    member_table = Table(member_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.8*inch])
    member_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(member_table)
    story.append(Spacer(1, 10))
    
    # Loan Information
    story.append(Paragraph("LOAN INFORMATION", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    loan_data = [
        [Paragraph("<b>Loan Number:</b>", label_style), Paragraph(f"{loan.loan_number}", value_style),
         Paragraph("<b>Loan Type:</b>", label_style), Paragraph(f"{loan.loan_product.name if loan.loan_product else 'N/A'}", value_style)],
        [Paragraph("<b>Interest Rate:</b>", label_style), Paragraph(f"{loan.interest_rate}% per annum", value_style),
         Paragraph("<b>Loan Term:</b>", label_style), Paragraph(f"{loan.term_months} months ({loan.term_days} days)", value_style)],
        [Paragraph("<b>Disbursement Date:</b>", label_style), Paragraph(f"{loan.disbursement_date.strftime('%B %d, %Y') if loan.disbursement_date else 'N/A'}", value_style),
         Paragraph("<b>Due Date:</b>", label_style), Paragraph(f"{loan.due_date.strftime('%B %d, %Y') if loan.due_date else 'N/A'}", value_style)],
        [Paragraph("<b>Monthly Payment:</b>", label_style), Paragraph(f"₱{loan.monthly_payment:,.2f}", value_style),
         Paragraph("<b>Payment Schedule:</b>", label_style), Paragraph(f"Monthly (Every {loan.due_date.day if loan.due_date else '30'}th of the month)", value_style)],
    ]
    loan_table = Table(loan_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.8*inch])
    loan_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(loan_table)
    story.append(Spacer(1, 10))
    
    # Payment Details
    story.append(Paragraph("PAYMENT DETAILS", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    payment_data = [
        [Paragraph("<b>Amount Paid:</b>", label_style), Paragraph(f"<font color='#1e3c72' size=12><b>₱{payment.amount:,.2f}</b></font>", amount_style),
         Paragraph("<b>Payment Method:</b>", label_style), Paragraph(f"{payment.get_payment_method_display()}", value_style)],
        [Paragraph("<b>Reference Number:</b>", label_style), Paragraph(f"{payment.reference_number or 'N/A'}", value_style),
         Paragraph("<b>Payment For:</b>", label_style), Paragraph(f"{loan.loan_number} - {loan.loan_product.name if loan.loan_product else 'Loan'}", value_style)],
    ]
    payment_table = Table(payment_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.8*inch])
    payment_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(payment_table)
    story.append(Spacer(1, 10))
    
    # Loan Summary
    story.append(Paragraph("LOAN SUMMARY", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    total_paid = loan.principal_amount - loan.remaining_balance
    paid_percentage = (total_paid / loan.principal_amount * 100) if loan.principal_amount > 0 else 0
    
    summary_data = [
        [Paragraph("<b>Original Principal:</b>", label_style), Paragraph(f"₱{loan.principal_amount:,.2f}", value_style),
         Paragraph("<b>Total Paid:</b>", label_style), Paragraph(f"₱{total_paid:,.2f}", value_style)],
        [Paragraph("<b>Remaining Balance:</b>", label_style), Paragraph(f"<font color='#dc2626'><b>₱{loan.remaining_balance:,.2f}</b></font>", amount_style),
         Paragraph("<b>Payment Progress:</b>", label_style), Paragraph(f"{paid_percentage:.1f}% Complete", value_style)],
        [Paragraph("<b>Next Due Date:</b>", label_style), Paragraph(f"{next_due_date.strftime('%B %d, %Y') if next_due_date else 'Fully Paid'}", value_style),
         Paragraph("<b>Next Payment Amount:</b>", label_style), Paragraph(f"₱{next_due_amount:,.2f}" if next_due_amount > 0 else "N/A", value_style)],
    ]
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.2*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    story.append(summary_table)
    story.append(Spacer(1, 10))
    
    # Payment History (last 3 payments)
    past_payments = Payment.objects.filter(loan=loan).order_by('-payment_date')[:3]
    if past_payments:
        story.append(Paragraph("RECENT PAYMENT HISTORY", header_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
        
        history_data = [["Date", "Amount", "Method", "Receipt #"]]
        for p in past_payments:
            history_data.append([
                p.payment_date.strftime('%Y-%m-%d'),
                f"₱{p.amount:,.2f}",
                p.get_payment_method_display(),
                p.payment_number
            ])
        
        history_table = Table(history_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        history_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3c72')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(history_table)
        story.append(Spacer(1, 10))
    
    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=5, spaceAfter=5))
    footer_text = """
    <para align=center fontSize=8 color=#6c757d>
    This is a system-generated receipt. No signature required.<br/>
    For inquiries, please contact TOMPuCO Cooperative at (035) 123-4567 or email support@tompuco.com<br/>
    Thank you for your payment!
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    story.append(Spacer(1, 10))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{payment.payment_number}.pdf"'
    return response
'''

# Find and replace the old function
pattern = r'def payment_receipt\(request, payment_id\).*?(?=\n@super_admin_required|\n\Z)'
content = re.sub(pattern, enhanced_receipt_func, content, flags=re.DOTALL)

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Enhanced receipt PDF with complete loan details')
