import os

middleware_content = '''
class RedirectManagerMiddleware:
    """Redirect managers from superadmin to manager portal"""
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=request.user)
                if profile.position.lower() == 'manager':
                    # If manager tries to access superadmin, redirect to manager dashboard
                    if request.path.startswith('/superadmin/'):
                        from django.shortcuts import redirect
                        return redirect('/manager/dashboard/')
            except:
                pass
        
        response = self.get_response(request)
        return response
'''

# Add to main/middleware.py
with open('main/middleware.py', 'w', encoding='utf-8') as f:
    f.write(middleware_content)
print('✓ Created middleware to redirect managers')
