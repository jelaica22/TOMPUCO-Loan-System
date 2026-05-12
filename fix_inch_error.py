import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the payment_receipt function by adding the missing import
fixed_receipt_func = '''

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
         Paragraph("<b>Transaction Date:</b>", label_style), Paragraph(f"{payment.payment_date.strftime('%B %d, %Y')}", value_style)],
    ]
    receipt_table = Table(receipt_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
    receipt_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(receipt_table)
    story.append(Spacer(1, 10))
    
    # Member Information
    story.append(Paragraph("MEMBER INFORMATION", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    member_data = [
        [Paragraph("<b>Member Name:</b>", label_style), Paragraph(f"{payment.member.first_name} {payment.member.last_name}", value_style),
         Paragraph("<b>Membership #:</b>", label_style), Paragraph(f"{payment.member.membership_number or 'N/A'}", value_style)],
    ]
    member_table = Table(member_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
    member_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(member_table)
    story.append(Spacer(1, 10))
    
    # Payment Details
    story.append(Paragraph("PAYMENT DETAILS", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    payment_data = [
        [Paragraph("<b>Amount Paid:</b>", label_style), Paragraph(f"<font color='#1e3c72' size=12><b>₱{payment.amount:,.2f}</b></font>", amount_style),
         Paragraph("<b>Payment Method:</b>", label_style), Paragraph(f"{payment.get_payment_method_display()}", value_style)],
        [Paragraph("<b>Loan Number:</b>", label_style), Paragraph(f"{loan.loan_number}", value_style),
         Paragraph("<b>Reference #:</b>", label_style), Paragraph(f"{payment.reference_number or 'N/A'}", value_style)],
    ]
    payment_table = Table(payment_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
    payment_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(payment_table)
    story.append(Spacer(1, 10))
    
    # Loan Summary
    story.append(Paragraph("LOAN SUMMARY", header_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=2, spaceAfter=10))
    
    summary_data = [
        [Paragraph("<b>Original Principal:</b>", label_style), Paragraph(f"₱{loan.principal_amount:,.2f}", value_style),
         Paragraph("<b>Remaining Balance:</b>", label_style), Paragraph(f"<font color='#dc2626'><b>₱{loan.remaining_balance:,.2f}</b></font>", amount_style)],
    ]
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 1.8*inch])
    summary_table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 8), ('BOTTOMPADDING', (0, 0), (-1, -1), 8)]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6'), spaceBefore=5, spaceAfter=5))
    footer_text = """
    <para align=center fontSize=8 color=#6c757d>
    This is a system-generated receipt. No signature required.<br/>
    For inquiries, please contact TOMPuCO Cooperative at (035) 123-4567 or email support@tompuco.com
    </para>
    """
    story.append(Paragraph(footer_text, styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{payment.payment_number}.pdf"'
    return response
'''

# Find and replace the old function
pattern = r'def payment_receipt\(request, payment_id\).*?(?=\n@super_admin_required|\n\Z)'
content = re.sub(pattern, fixed_receipt_func, content, flags=re.DOTALL)

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Fixed payment_receipt function - added missing inch import')
