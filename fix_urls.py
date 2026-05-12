with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Ensure the URL pattern is correct
if "path('loan-products/<int:product_id>/', views.loan_product_detail, name='loan_product_detail')" not in content:
    # Add the pattern before the edit pattern
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if "path('loan-products/<int:product_id>/edit/'" in line:
            new_lines.append("    path('loan-products/<int:product_id>/', views.loan_product_detail, name='loan_product_detail'),")
        new_lines.append(line)
    
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print('✓ Added loan_product_detail URL')
else:
    print('URL already exists')
