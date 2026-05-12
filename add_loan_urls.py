with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('loans/create/'" not in content:
    new_urls = """
    path('loans/create/', views.loan_create, name='loan_create'),
    path('loans/<int:loan_id>/', views.loan_detail, name='loan_detail'),
    path('loans/<int:loan_id>/edit/', views.loan_edit, name='loan_edit'),
    path('loans/<int:loan_id>/payment/', views.loan_payment, name='loan_payment'),
    path('loans/<int:loan_id>/delete/', views.loan_delete, name='loan_delete'),
"""
    content = content.replace(
        "path('loans/', views.loans_list, name='loans_list'),",
        "path('loans/', views.loans_list, name='loans_list'),\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added loan management URLs')
