import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_dashboard = '''@super_admin_required
def dashboard(request):
    """Super Admin Dashboard with analytics"""
    from django.contrib.auth.models import User
    from main.models import Member, LoanApplication, Loan, Payment, LoanProduct
    from django.db.models import Sum
    from datetime import datetime, timedelta
    
    # Basic Stats
    total_users = User.objects.count()
    total_members = Member.objects.count()
    total_applications = LoanApplication.objects.count()
    active_loans = Loan.objects.filter(status="active").count()
    
    # Financial Stats
    total_loan_amount = Loan.objects.aggregate(total=Sum("principal_amount"))["total"] or 0
    total_payments = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    collection_rate = (total_payments / total_loan_amount * 100) if total_loan_amount > 0 else 0
    loan_products_count = LoanProduct.objects.count()
    
    # Recent Users (last 5)
    recent_users = User.objects.order_by("-date_joined")[:5]
    
    # Chart Data - User Growth (last 7 days)
    user_growth_labels = []
    user_growth_data = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        user_growth_labels.append(date.strftime("%a"))
        count = User.objects.filter(date_joined__date=date).count()
        user_growth_data.append(count)
    
    # Member Distribution
    active_members = Member.objects.filter(is_active=True).count()
    inactive_members = Member.objects.filter(is_active=False).count()
    
    context = {
        "total_users": total_users,
        "total_members": total_members,
        "total_applications": total_applications,
        "active_loans": active_loans,
        "total_loan_amount": total_loan_amount,
        "total_payments": total_payments,
        "collection_rate": round(collection_rate, 1),
        "loan_products_count": loan_products_count,
        "recent_users": recent_users,
        "user_growth_labels": user_growth_labels,
        "user_growth_data": user_growth_data,
        "member_distribution_labels": ["Active Members", "Inactive Members"],
        "member_distribution_data": [active_members, inactive_members],
    }
    return render(request, "admin_panel/dashboard.html", context)'''

# Find and replace the dashboard function
pattern = r'def dashboard\(request\).*?(?=\n@super_admin_required|\n\Z)'
content = re.sub(pattern, new_dashboard, content, flags=re.DOTALL)

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Updated dashboard view with analytics data')
