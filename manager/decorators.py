from django.shortcuts import redirect
from django.contrib import messages

def manager_required(view_func):
    '''Decorator to check if user has manager privileges'''
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('main:login')
        
        from .models import ManagerProfile
        try:
            manager = request.user.manager_profile
            if manager:
                return view_func(request, *args, **kwargs)
        except ManagerProfile.DoesNotExist:
            pass
        
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'Access denied. Manager privileges required.')
        return redirect('main:dashboard')
    
    return wrapper
