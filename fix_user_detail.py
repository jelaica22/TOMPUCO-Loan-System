import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if the function exists
if 'def user_detail' in content:
    # Replace the entire user_detail function using regex
    pattern = r'@super_admin_required\s+def user_detail\(request, user_id\):.*?(?=@super_admin_required|\Z)'
    
    new_func = '''@super_admin_required
def user_detail(request, user_id):
    """View user details"""
    from django.http import JsonResponse
    user = get_object_or_404(User, id=user_id)
    # Always return JSON for API calls (AJAX request from modal)
    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
        "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else None,
        "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M"),
    })
'''
    
    content = re.sub(pattern, new_func, content, flags=re.DOTALL)
    
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Fixed user_detail view to always return JSON')
else:
    print('user_detail function not found, adding it...')
    # Add the function at the end of the file
    new_func = '''

@super_admin_required
def user_detail(request, user_id):
    """View user details"""
    from django.http import JsonResponse
    user = get_object_or_404(User, id=user_id)
    return JsonResponse({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "is_active": user.is_active,
        "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else None,
        "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M"),
    })
'''
    content = content + new_func
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added user_detail view')
