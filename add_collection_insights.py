import sys
sys.path.insert(0, '.')

with open('manager/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add collection rate breakdown
collection_insight = '''

def get_collection_insights(request):
    from django.db.models import Sum
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    
    # Monthly collection trends
    monthly_data = []
    for i in range(6):
        month_start = datetime(today.year, today.month - i, 1).date()
        month_end = datetime(today.year, today.month - i + 1, 1).date() - timedelta(days=1)
        total = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_data.append({
            'month': month_start.strftime('%B'),
            'amount': total
        })
    
    return JsonResponse({
        'monthly_trends': monthly_data,
        'collection_rate': calculate_collection_rate(),
        'target_rate': 70,
        'gap': max(0, 70 - calculate_collection_rate())
    })
'''
