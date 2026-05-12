with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_login = '''
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.shortcuts import render, redirect

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # FIRST: Check StaffProfile for specific roles
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=user)
                role = profile.position.lower()
                
                # Manager goes to Manager Portal
                if role == 'manager':
                    return redirect('/manager/dashboard/')
                # Cashier goes to Cashier Portal
                elif role == 'cashier':
                    return redirect('/cashier/dashboard/')
                # Committee goes to Committee Portal
                elif role == 'committee':
                    return redirect('/committee/dashboard/')
                # Staff goes to Staff Portal
                elif role == 'staff':
                    return redirect('/staff/dashboard/')
            except:
                pass
            
            # SECOND: Super Admin (only if no specific role found)
            if user.is_superuser:
                return redirect('/superadmin/')
            
            # THIRD: Staff
            if user.is_staff:
                return redirect('/staff/dashboard/')
            
            # FOURTH: Member
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'main/login.html')
'''

import re
pattern = r'def user_login\(request\).*?(?=\n@login_required|\n\Z|$)'
content = re.sub(pattern, new_login, content, flags=re.DOTALL)

with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated login - StaffProfile checked BEFORE superuser')
