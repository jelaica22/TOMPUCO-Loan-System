with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing auth views
auth_views = '''

@login_required
@staff_required
def change_password(request):
    """Change staff password"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Password changed successfully! Please login again.')
            return redirect('/')
    else:
        return render(request, 'staff/change_password.html')
    
    return redirect('staff:staff_profile')


@login_required
@staff_required
def edit_profile(request):
    """Edit staff profile"""
    profile, created = StaffProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.phone_number = request.POST.get('phone_number', '')
        profile.department = request.POST.get('department', '')
        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('staff:staff_profile')
    
    return redirect('staff:staff_profile')
'''

if 'def change_password' not in content:
    content = content + auth_views
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added change_password and edit_profile views')
