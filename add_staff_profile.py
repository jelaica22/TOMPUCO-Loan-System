with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing staff_profile view
staff_profile_view = '''

@login_required
@staff_required
def staff_profile(request):
    """Staff profile page"""
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    return render(request, 'staff/profile.html', {'staff_profile': profile})
'''

if 'def staff_profile' not in content:
    content = content + staff_profile_view
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added staff_profile view')
