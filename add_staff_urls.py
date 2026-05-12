with open('staff/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing URL patterns
new_patterns = """
    path('profile/', views.staff_profile, name='staff_profile'),
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
"""

if "path('profile/'" not in content:
    content = content.replace(
        "urlpatterns = [",
        "urlpatterns = [\n" + new_patterns
    )
    with open('staff/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added missing URL patterns to staff')
