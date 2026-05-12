with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('payments/create/'" not in content:
    new_urls = """
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:payment_id>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('payments/<int:payment_id>/delete/', views.payment_delete, name='payment_delete'),
"""
    content = content.replace(
        "path('payments/', views.payments_list, name='payments_list'),",
        "path('payments/', views.payments_list, name='payments_list'),\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added payment URLs')
