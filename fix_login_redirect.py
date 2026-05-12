import re

with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the login redirect logic and update it
new_login_logic = '''
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check for Manager role first (before staff)
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=user)
                if profile.position.lower() == 'manager':
                    return redirect('/manager/dashboard/')
            except:
                pass
            
            # Then check for Super Admin
            if user.is_superuser:
                return redirect('/superadmin/')
            
            # Then check for Staff
            if user.is_staff:
                return redirect('/staff/dashboard/')
            
            # Default to member dashboard
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'main/login.html')
'''

# Find existing login function and replace
if 'def user_login' in content:
    import re
    pattern = r'def user_login\(request\).*?(?=\ndef |\Z)'
    content = re.sub(pattern, new_login_logic, content, flags=re.DOTALL)
    with open('main/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Updated login redirect - Manager checked first')
