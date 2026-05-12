import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add context processor-like functionality to profile view
profile_update = '''

@super_admin_required
def profile(request):
    from main.models import AuditLog, StaffProfile
    from django.contrib.auth.models import User
    from datetime import date
    
    # Get or create staff profile
    staff_profile, created = StaffProfile.objects.get_or_create(user=request.user)
    
    # Get stats for the profile
    total_users = User.objects.count()
    total_members = Member.objects.count()
    
    # Calculate days active (since first login)
    first_login = request.user.last_login
    if first_login:
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
        'staff_profile': staff_profile,
    })'''

# Replace the old profile function
pattern = r'def profile\(request\).*?(?=\n@super_admin_required|\n\Z)'
content = re.sub(pattern, profile_update, content, flags=re.DOTALL)

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated profile view to include staff_profile')
