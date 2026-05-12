import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add profile management functions
profile_functions = '''

@super_admin_required
def profile(request):
    from main.models import AuditLog
    from django.contrib.auth.models import User
    from django.db.models import Count
    
    # Get stats for the profile
    total_users = User.objects.count()
    total_members = Member.objects.count()
    
    # Calculate days active (since first login)
    first_login = request.user.last_login
    if first_login:
        from datetime import date
        days_active = (date.today() - first_login.date()).days
    else:
        days_active = 0
    
    # Get recent activity logs
    recent_logs = AuditLog.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    return render(request, 'admin_panel/profile.html', {
        'total_users': total_users,
        'total_members': total_members,
        'days_active': days_active,
        'recent_logs': recent_logs,
    })


@super_admin_required
def upload_avatar(request):
    from main.models import StaffProfile
    if request.method == 'POST' and request.FILES.get('avatar'):
        profile, created = StaffProfile.objects.get_or_create(user=request.user)
        profile.profile_picture = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Profile picture updated successfully!')
    return redirect('admin_panel:profile')


@super_admin_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.username = request.POST.get('username', user.username)
        user.save()
        messages.success(request, 'Profile information updated successfully!')
    return redirect('admin_panel:profile')


@super_admin_required
def change_password(request):
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.hashers import check_password
    
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check current password
        if not check_password(current_password, request.user.password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully!')
    
    return redirect('admin_panel:profile')
'''

# Add the functions
content = content + profile_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added profile management functions')
