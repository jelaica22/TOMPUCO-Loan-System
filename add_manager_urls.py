import sys
sys.path.insert(0, '.')

with open('manager/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add monitoring URLs
new_urls = '''
    # Staff Monitoring (View Only)
    path('staff-applications/', views.staff_applications, name='staff_applications'),
    path('staff-loans/', views.staff_loans, name='staff_loans'),
    path('staff-payments/', views.staff_payments, name='staff_payments'),
    path('payment-instructions/', views.payment_instructions, name='payment_instructions'),
    path('restructuring-requests/', views.restructuring_requests, name='restructuring_requests'),
'''

if "path('staff-applications/'" not in content:
    content = content.replace(
        "urlpatterns = [",
        "urlpatterns = [" + new_urls
    )
    with open('manager/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added monitoring URLs to manager/urls.py')
