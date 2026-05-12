with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('loan-applications/create/'" not in content:
    new_urls = """
    path('loan-applications/create/', views.loan_application_create, name='loan_application_create'),
    path('loan-applications/<int:app_id>/edit/', views.loan_application_edit, name='loan_application_edit'),
"""
    # Insert after loan-applications list
    content = content.replace(
        "path('loan-applications/', views.loan_applications_list, name='loan_applications_list'),",
        "path('loan-applications/', views.loan_applications_list, name='loan_applications_list'),\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added create and edit URLs')
