with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Create a completely new login view
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
            
            # FIRST: Check StaffProfile for role
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=user)
                role = profile.position.lower()
                
                print(f"DEBUG: User {username} has role: {role}")  # Debug output
                
                if role == 'manager':
                    print("DEBUG: Redirecting to Manager Portal")
                    return redirect('/manager/dashboard/')
                elif role == 'cashier':
                    return redirect('/cashier/dashboard/')
                elif role == 'committee':
                    return redirect('/committee/dashboard/')
                elif role == 'staff':
                    return redirect('/staff/dashboard/')
            except Exception as e:
                print(f"DEBUG: No StaffProfile found: {e}")
                pass
            
            # SECOND: Super Admin
            if user.is_superuser:
                return redirect('/superadmin/')
            
            # THIRD: Regular member
            return redirect('/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'main/login.html')
'''

# Find and replace the login function
import re
pattern = r'def user_login\(request\).*?(?=\n@login_required|\n\Z|$)'
content = re.sub(pattern, new_login, content, flags=re.DOTALL)

with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated login view - now checks StaffProfile first')
