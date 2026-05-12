with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('payment-schedules/generate/'" not in content:
    new_urls = """
    path('payment-schedules/generate/', views.payment_schedule_generate, name='payment_schedule_generate'),
    path('payment-schedules/<int:schedule_id>/', views.payment_schedule_detail, name='payment_schedule_detail'),
    path('payment-schedules/<int:schedule_id>/edit/', views.payment_schedule_edit, name='payment_schedule_edit'),
    path('payment-schedules/<int:schedule_id>/mark-paid/', views.payment_schedule_mark_paid, name='payment_schedule_mark_paid'),
    path('payment-schedules/<int:schedule_id>/delete/', views.payment_schedule_delete, name='payment_schedule_delete'),
"""
    content = content.replace(
        "path('payment-schedules/', views.payment_schedules_list, name='payment_schedules_list'),",
        "path('payment-schedules/', views.payment_schedules_list, name='payment_schedules_list'),\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added payment schedule URLs')
