with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('loan-attachments/create/'" not in content:
    new_urls = """
    path('loan-attachments/create/', views.loan_attachment_create, name='loan_attachment_create'),
    path('loan-attachments/<int:att_id>/', views.loan_attachment_detail, name='loan_attachment_detail'),
    path('loan-attachments/<int:att_id>/delete/', views.loan_attachment_delete, name='loan_attachment_delete'),
"""
    content = content.replace(
        "path('loan-attachments/', views.loan_attachments_list, name='loan_attachments_list'),",
        "path('loan-attachments/', views.loan_attachments_list, name='loan_attachments_list'),\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added loan attachment URLs')
