with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

reports_function = '''

@super_admin_required
def reports(request):
    """Reports and Analytics page"""
    from django.db.models import Sum
    from main.models import Member, Loan, Payment
    
    total_members = Member.objects.count()
    total_loans = Loan.objects.count()
    total_disbursed = Loan.objects.aggregate(total=Sum("principal_amount"))["total"] or 0
    total_payments = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    collection_rate = (total_payments / total_disbursed * 100) if total_disbursed > 0 else 0
    
    context = {
        "total_members": total_members,
        "total_loans": total_loans,
        "total_disbursed": total_disbursed,
        "collection_rate": round(collection_rate, 1),
    }
    return render(request, "admin_panel/reports.html", context)
'''

# Check if reports function already exists
if 'def reports' not in content:
    content = content + reports_function
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added reports view function')
else:
    print('✓ Reports view function already exists')
