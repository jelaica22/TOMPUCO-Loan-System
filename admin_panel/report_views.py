from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from main.models import Member, LoanApplication, Loan, Payment, LoanProduct

@staff_member_required
def reports_api(request, report_type):
    """API endpoint for generating reports"""
    
    # Get date filters
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    
    try:
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            date_from = None
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            date_to = timezone.now().date()
    except:
        date_from = None
        date_to = timezone.now().date()
    
    if report_type == 'member_report':
        members = Member.objects.all()
        data = {
            'success': True,
            'title': 'Member Report',
            'headers': ['ID', 'Membership #', 'Name', 'Contact', 'Email', 'Join Date', 'Status'],
            'rows': []
        }
        for m in members:
            data['rows'].append([
                m.id,
                m.membership_number or '-',
                f"{m.first_name} {m.last_name}",
                m.contact_number or '-',
                m.user.email if m.user else '-',
                m.created_at.strftime('%Y-%m-%d') if m.created_at else '-',
                'Active' if m.is_active else 'Inactive'
            ])
        return JsonResponse(data)
    
    elif report_type == 'loan_report':
        loans = Loan.objects.all()
        data = {
            'success': True,
            'title': 'Loan Summary Report',
            'headers': ['Loan #', 'Member', 'Principal', 'Balance', 'Interest Rate', 'Status', 'Disbursement Date'],
            'rows': []
        }
        for l in loans:
            data['rows'].append([
                l.loan_number,
                f"{l.borrower.first_name} {l.borrower.last_name}" if l.borrower else '-',
                f"₱{l.principal_amount:,.2f}",
                f"₱{l.remaining_balance:,.2f}",
                f"{l.interest_rate}%",
                l.status,
                l.disbursement_date.strftime('%Y-%m-%d') if l.disbursement_date else '-'
            ])
        return JsonResponse(data)
    
    elif report_type == 'payment_report':
        payments = Payment.objects.all()
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)
        
        data = {
            'success': True,
            'title': f'Payment Report {"(" + date_from.strftime("%Y-%m-%d") + " to " + date_to.strftime("%Y-%m-%d") + ")" if date_from else ""}',
            'headers': ['Date', 'Payment #', 'Member', 'Loan #', 'Amount', 'Method', 'Status'],
            'rows': []
        }
        for p in payments[:100]:  # Limit to 100 for performance
            data['rows'].append([
                p.payment_date.strftime('%Y-%m-%d') if p.payment_date else '-',
                p.payment_number,
                f"{p.member.first_name} {p.member.last_name}" if p.member else '-',
                p.loan.loan_number if p.loan else '-',
                f"₱{p.amount:,.2f}",
                p.get_payment_method_display() if hasattr(p, 'get_payment_method_display') else p.payment_method,
                p.status
            ])
        return JsonResponse(data)
    
    elif report_type == 'application_report':
        applications = LoanApplication.objects.all()
        data = {
            'success': True,
            'title': 'Loan Application Report',
            'headers': ['App ID', 'Member', 'Loan Type', 'Requested Amount', 'Approved Line', 'Status', 'Date'],
            'rows': []
        }
        for a in applications[:100]:
            data['rows'].append([
                a.application_id,
                f"{a.member.first_name} {a.member.last_name}" if a.member else '-',
                a.loan_product.name if a.loan_product else '-',
                f"₱{a.requested_amount:,.2f}" if a.requested_amount else '-',
                f"₱{a.approved_line:,.2f}" if a.approved_line else '-',
                a.status,
                a.created_at.strftime('%Y-%m-%d') if a.created_at else '-'
            ])
        return JsonResponse(data)
    
    elif report_type == 'aging_report':
        # Calculate aging buckets
        today = timezone.now().date()
        loans = Loan.objects.filter(status='active')
        
        aging_data = {
            '0-30': {'count': 0, 'amount': 0},
            '31-60': {'count': 0, 'amount': 0},
            '61-90': {'count': 0, 'amount': 0},
            '90+': {'count': 0, 'amount': 0}
        }
        
        for loan in loans:
            if loan.due_date:
                days_overdue = (today - loan.due_date).days
                if days_overdue > 0:
                    if days_overdue <= 30:
                        aging_data['0-30']['count'] += 1
                        aging_data['0-30']['amount'] += loan.remaining_balance
                    elif days_overdue <= 60:
                        aging_data['31-60']['count'] += 1
                        aging_data['31-60']['amount'] += loan.remaining_balance
                    elif days_overdue <= 90:
                        aging_data['61-90']['count'] += 1
                        aging_data['61-90']['amount'] += loan.remaining_balance
                    else:
                        aging_data['90+']['count'] += 1
                        aging_data['90+']['amount'] += loan.remaining_balance
        
        data = {
            'success': True,
            'title': 'Aging Report - Past Due Loans',
            'headers': ['Days Overdue', 'Number of Loans', 'Total Amount', 'Percentage'],
            'rows': []
        }
        total_amount = sum(v['amount'] for v in aging_data.values())
        for bucket, values in aging_data.items():
            percentage = (values['amount'] / total_amount * 100) if total_amount > 0 else 0
            data['rows'].append([f"{bucket} days", values['count'], f"₱{values['amount']:,.2f}", f"{percentage:.1f}%"])
        
        return JsonResponse(data)
    
    elif report_type == 'collection_report':
        # Group payments by date
        payments = Payment.objects.filter(status='completed')
        if date_from:
            payments = payments.filter(payment_date__gte=date_from)
        if date_to:
            payments = payments.filter(payment_date__lte=date_to)
        
        # Group by date
        from collections import defaultdict
        daily_collections = defaultdict(lambda: {'count': 0, 'amount': 0})
        
        for p in payments:
            if p.payment_date:
                date_key = p.payment_date.strftime('%Y-%m-%d')
                daily_collections[date_key]['count'] += 1
                daily_collections[date_key]['amount'] += p.amount
        
        data = {
            'success': True,
            'title': f'Collection Report',
            'headers': ['Date', 'Number of Payments', 'Total Amount'],
            'rows': []
        }
        for date_key in sorted(daily_collections.keys(), reverse=True)[:30]:
            values = daily_collections[date_key]
            data['rows'].append([date_key, values['count'], f"₱{values['amount']:,.2f}"])
        
        return JsonResponse(data)
    
    elif report_type == 'product_report':
        products = LoanProduct.objects.all()
        data = {
            'success': True,
            'title': 'Loan Product Performance Report',
            'headers': ['Product Name', 'Applications', 'Approved', 'Active Loans', 'Total Disbursed'],
            'rows': []
        }
        for p in products:
            applications = LoanApplication.objects.filter(loan_product=p).count()
            approved = LoanApplication.objects.filter(loan_product=p, status='approved').count()
            active_loans = Loan.objects.filter(loan_product=p, status='active').count()
            total_disbursed = Loan.objects.filter(loan_product=p).aggregate(total=Sum('principal_amount'))['total'] or 0
            
            data['rows'].append([
                p.display_name or p.name,
                applications,
                approved,
                active_loans,
                f"₱{total_disbursed:,.2f}"
            ])
        return JsonResponse(data)
    
    elif report_type == 'financial_report':
        total_loans = Loan.objects.aggregate(total=Sum('principal_amount'))['total'] or 0
        total_payments = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        outstanding = total_loans - total_payments
        total_members = Member.objects.count()
        active_loans = Loan.objects.filter(status='active').count()
        
        data = {
            'success': True,
            'title': 'Financial Summary Report',
            'headers': ['Category', 'Amount', 'Notes'],
            'rows': [
                ['Total Loan Disbursements', f"₱{total_loans:,.2f}", 'All loans issued'],
                ['Total Payments Received', f"₱{total_payments:,.2f}", f'{ (total_payments/total_loans*100) if total_loans > 0 else 0:.1f}% collection rate'],
                ['Outstanding Balance', f"₱{outstanding:,.2f}", 'Remaining to collect'],
                ['Active Loans', str(active_loans), f'{active_loans} active loans'],
                ['Total Members', str(total_members), 'Registered members']
            ]
        }
        return JsonResponse(data)
    
    else:
        return JsonResponse({'success': False, 'error': 'Invalid report type'})
