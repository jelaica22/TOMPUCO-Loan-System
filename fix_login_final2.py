with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Completely replace the login function
login_code = '''
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
            
            # CRITICAL: Check StaffProfile FIRST before anything else
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=user)
                role = profile.position.lower()
                
                # Role-based redirects - these take priority
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
            
            # Only check superuser if no StaffProfile role found
            if user.is_superuser:
                return redirect('/superadmin/')
            
            if user.is_staff:
                return redirect('/staff/dashboard/')
            
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'main/login.html')
'''

# Find and replace the login function
import re
pattern = r'def user_login\(request\).*?(?=\n@login_required|\n\Z|$)'
content = re.sub(pattern, login_code, content, flags=re.DOTALL)

with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated login view - StaffProfile checked FIRST')
