with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add upload profile picture view
upload_view = '''

@login_required
@staff_required
def upload_profile_picture(request):
    """Upload profile picture"""
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        profile, created = StaffProfile.objects.get_or_create(user=request.user)
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, 'Profile picture updated successfully!')
    return redirect('staff:staff_profile')
'''

if 'def upload_profile_picture' not in content:
    content = content + upload_view
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added upload_profile_picture view')
