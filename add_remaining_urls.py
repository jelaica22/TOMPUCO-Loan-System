import re

with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing URL patterns for Tables 11-14
new_urls = """
    # Table 11: Committee Decisions
    path('committee-decisions/<int:decision_id>/', views.committee_decision_detail, name='committee_decision_detail'),
    path('committee-decisions/<int:decision_id>/delete/', views.committee_decision_delete, name='committee_decision_delete'),
    
    # Table 12: Notifications
    path('notifications/<int:notif_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:notif_id>/delete/', views.notification_delete, name='notification_delete'),
    
    # Table 13: Audit Logs
    path('audit-logs/<int:log_id>/', views.audit_log_detail, name='audit_log_detail'),
"""

if "path('committee-decisions/" not in content:
    content = content.replace(
        "path('committee-decisions/', views.committee_decisions_list, name='committee_decisions_list'),",
        "path('committee-decisions/', views.committee_decisions_list, name='committee_decisions_list'),\n" + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added URL patterns for Tables 11-14')
