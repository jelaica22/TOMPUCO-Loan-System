with open('manager/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_decorator = '''
def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        
        # Check for manager role in StaffProfile
        try:
            from main.models import StaffProfile
            profile = StaffProfile.objects.get(user=request.user)
            if profile.position.lower() == 'manager':
                return view_func(request, *args, **kwargs)
        except:
            pass
        
        # Super admin fallback
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Access denied. Manager access required.')
        return redirect('/')
    return wrapper
'''

import re
pattern = r'def manager_required\(view_func\).*?return wrapper'
content = re.sub(pattern, new_decorator, content, flags=re.DOTALL)

with open('manager/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated manager_required decorator')
