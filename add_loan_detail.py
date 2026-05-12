import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add loan_product_detail function if not exists
if 'def loan_product_detail' not in content:
    loan_detail_func = '''

@super_admin_required
def loan_product_detail(request, product_id):
    """View loan product details"""
    from django.http import JsonResponse
    product = get_object_or_404(LoanProduct, id=product_id)
    return JsonResponse({
        "id": product.id,
        "name": product.name,
        "display_name": product.display_name,
        "description": getattr(product, "description", ""),
        "interest_rate": str(product.interest_rate),
        "term_months": product.term_months,
        "term_days": getattr(product, "term_days", product.term_months * 30),
        "min_amount": str(product.min_amount),
        "max_amount": str(product.max_amount),
        "is_active": product.is_active,
        "created_at": product.created_at.strftime("%Y-%m-%d %H:%M") if hasattr(product, "created_at") and product.created_at else None,
    })
'''
    content = content + loan_detail_func
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added loan_product_detail view')
else:
    print('loan_product_detail view already exists')
