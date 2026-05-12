with open('staff/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('disbursement/'" not in content:
    new_urls = """
    path('disbursement/', views.disbursement, name='staff_disbursement'),
    path('api/application/<int:app_id>/details/', views.application_details, name='application_details'),
    path('api/application/<int:app_id>/disburse/', views.disburse_loan, name='disburse_loan'),
"""
    content = content.replace(
        "urlpatterns = [",
        "urlpatterns = [\n" + new_urls
    )
    with open('staff/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added disbursement URLs to staff')
