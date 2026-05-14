from django.shortcuts import redirect
from django.urls import reverse


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')

        # Check if user has staff profile
        if not hasattr(request.user, 'staff_profile'):
            return redirect('/login/')

        return view_func(request, *args, **kwargs)

    return wrapper