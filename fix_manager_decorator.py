import re

with open('manager/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update manager_required decorator
new_decorator = '''
def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')
        # Super Admin can also access manager portal
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        # Check if user has staff profile with Manager position
        if request.user.is_staff:
            from main.models import StaffProfile
            try:
                profile = StaffProfile.objects.get(user=request.user)
                if profile.position.lower() == 'manager':
                    return view_func(request, *args, **kwargs)
            except:
                pass
        messages.error(request, 'Access denied. Manager access required.')
        return redirect('/')
    return wrapper
'''

# Replace the old decorator
pattern = r'def manager_required\(view_func\).*?return wrapper'
content = re.sub(pattern, new_decorator, content, flags=re.DOTALL)

with open('manager/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated manager_required decorator')
