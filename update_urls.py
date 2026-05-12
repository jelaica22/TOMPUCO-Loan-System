import re

with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'loan-products/<int:product_id>/' not in content:
    # Add the detail URL before edit
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if "path('loan-products/<int:product_id>/edit/'" in line:
            new_lines.append("    path('loan-products/<int:product_id>/', views.loan_product_detail, name='loan_product_detail'),")
    
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('✓ Added loan_product_detail URL')
else:
    print('loan_product_detail URL already exists')
