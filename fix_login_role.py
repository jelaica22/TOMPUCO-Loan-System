import re

with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_login_logic = '''
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check user role from StaffProfile
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=user)
                role = profile.position.lower()
                
                if role == 'manager':
                    return redirect('/manager/dashboard/')
                elif role == 'cashier':
                    return redirect('/cashier/dashboard/')
                elif role == 'committee':
                    return redirect('/committee/dashboard/')
                elif role == 'staff':
                    return redirect('/staff/dashboard/')
            except:
                pass
            
            # Super Admin
            if user.is_superuser:
                return redirect('/superadmin/')
            
            # Member
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'main/login.html')
'''

# Replace the login function
pattern = r'def user_login\(request\).*?(?=\ndef |\Z)'
if 'def user_login' in content:
    content = re.sub(pattern, new_login_logic, content, flags=re.DOTALL)
    with open('main/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Updated login redirect based on StaffProfile role')
