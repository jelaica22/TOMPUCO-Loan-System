from django.shortcuts import redirect
from functools import wraps


def cashier_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')

        # Check if user has cashier_profile attribute
        if not hasattr(request.user, 'cashier_profile'):
            return redirect('/login/')

        # Check if cashier profile is active
        if not request.user.cashier_profile.is_active:
            return redirect('/login/')

        return view_func(request, *args, **kwargs)

    return wrapper