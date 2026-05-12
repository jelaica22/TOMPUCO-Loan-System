import re

with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing URL patterns
new_urls = """
    # Table 12: Notifications
    path('notifications/<int:notif_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:notif_id>/delete/', views.notification_delete, name='notification_delete'),
    
    # Table 13: Audit Logs
    path('audit-logs/<int:log_id>/', views.audit_log_detail, name='audit_log_detail'),
    
    # Table 14: System Settings
    path('system-settings/<int:setting_id>/update/', views.system_setting_update, name='system_setting_update'),
"""

if "path('notifications/<int:notif_id>/read/'" not in content:
    # Find the notifications line and add after it
    content = content.replace(
        "path('notifications/', views.notifications_list, name='notifications_list'),",
        "path('notifications/', views.notifications_list, name='notifications_list'),\n" + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added URL patterns for Tables 11-14')
