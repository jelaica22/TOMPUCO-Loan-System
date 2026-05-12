from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages


def cashier_required(view_func):
    """Decorator to check if user is cashier"""

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('main:login')

        # Check if user has cashier role
        if request.user.groups.filter(name='Cashier').exists() or request.user.is_staff:
            return view_func(request, *args, **kwargs)

        messages.error(request, 'Access denied. Cashier privileges required.')
        return redirect('main:dashboard')

    return wrapper

