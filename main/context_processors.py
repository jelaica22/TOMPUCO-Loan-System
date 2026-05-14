from django.db import connection
from django.conf import settings  # ✅ ADD THIS IMPORT


def member_profile(request):
    context = {}

    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'member_profile'):
                member = request.user.member_profile
                context['member'] = member
        except Exception as e:
            print(f"Member profile error: {e}")

    return context


def staff_profile_context(request):
    """Add staff profile to context if user is staff"""
    context = {}

    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            from main.models import StaffProfile
            if hasattr(request.user, 'staff_profile'):
                context['staff_profile'] = request.user.staff_profile
        except:
            pass

    return context


def manager_profile(request):
    """Add manager profile to context if user is manager"""
    context = {}

    if request.user.is_authenticated:
        try:
            from main.models import StaffProfile
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
                if hasattr(profile, 'position') and profile.position == 'manager':
                    context['is_manager'] = True
                    context['manager_profile'] = profile
        except:
            pass

    return context


def cashier_profile(request):
    """Add cashier profile to context if user is cashier"""
    context = {}

    if request.user.is_authenticated:
        try:
            from main.models import StaffProfile
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
                if hasattr(profile, 'position') and profile.position == 'cashier':
                    context['is_cashier'] = True
                    context['cashier_profile'] = profile
        except:
            pass

    return context


def admin_profile(request):
    """Add admin profile to context if user is admin"""
    context = {}

    if request.user.is_authenticated and request.user.is_superuser:
        context['is_admin'] = True

    return context


# ✅ ADD THIS NEW FUNCTION AT THE BOTTOM
def recaptcha_site_key(request):
    """
    Add reCAPTCHA site key to all templates.
    This makes {{ RECAPTCHA_SITE_KEY }} available globally.
    """
    return {
        'RECAPTCHA_SITE_KEY': settings.RECAPTCHA_PUBLIC_KEY
    }