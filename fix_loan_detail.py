import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the loan_product_detail function with a working version
loan_detail_func = '''
@super_admin_required
def loan_product_detail(request, product_id):
    """View loan product details - returns JSON"""
    from django.http import JsonResponse
    from main.models import LoanProduct
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

# Remove existing function if present and add new one
if 'def loan_product_detail' in content:
    # Remove old function
    pattern = r'def loan_product_detail\(request, product_id\):.*?(?=\n@super_admin_required|\n\Z)'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    
# Add at the end of file
content = content + '\n' + loan_detail_func

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added/Updated loan_product_detail view')
