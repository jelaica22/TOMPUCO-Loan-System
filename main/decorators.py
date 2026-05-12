# main/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('main:login')
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('main:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('main:login')
        if not (request.user.is_superuser or request.user.groups.filter(name='Manager').exists()):
            return redirect('main:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.groups.filter(name='Staff').exists()),
        login_url='/staff/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def committee_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.groups.filter(name='Committee').exists(),
        login_url='/staff/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def cashier_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.groups.filter(name='Cashier').exists(),
        login_url='/staff/login/'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator