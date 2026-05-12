with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('profile/'" not in content:
    new_urls = """
    path('profile/', views.profile, name='profile'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
"""
    content = content.replace(
        "urlpatterns = [",
        "urlpatterns = [\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added profile URLs')
