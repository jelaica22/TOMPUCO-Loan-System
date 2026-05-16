from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist


def member_profile(request):
    """
    Add member profile to context if user is a member
    """
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
    """
    Add staff profile to context if user is staff
    """
    context = {}

    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            from staff.models import StaffProfile
            if hasattr(request.user, 'staff_profile'):
                context['staff_profile'] = request.user.staff_profile
        except Exception as e:
            print(f"Staff profile error: {e}")

    return context


def manager_profile(request):
    """
    Add manager profile to context if user is manager
    """
    context = {}

    if request.user.is_authenticated:
        try:
            from staff.models import StaffProfile
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
                if hasattr(profile, 'position') and profile.position == 'manager':
                    context['is_manager'] = True
                    context['manager_profile'] = profile
        except Exception as e:
            print(f"Manager profile error: {e}")

    return context


def cashier_profile(request):
    """
    Add cashier profile to context if user is cashier
    """
    context = {}

    if request.user.is_authenticated:
        try:
            from staff.models import StaffProfile
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
                if hasattr(profile, 'position') and profile.position == 'cashier':
                    context['is_cashier'] = True
                    context['cashier_profile'] = profile
        except Exception as e:
            print(f"Cashier profile error: {e}")

    return context


def admin_profile(request):
    """
    Add admin profile to context if user is superuser
    """
    context = {}

    if request.user.is_authenticated and request.user.is_superuser:
        context['is_admin'] = True
        context['is_superuser'] = True

    return context


def recaptcha_site_key(request):
    """
    Add reCAPTCHA site key to all templates.
    This makes {{ RECAPTCHA_SITE_KEY }} available globally.
    """
    # Try multiple possible setting names for compatibility
    site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', None)

    if not site_key:
        site_key = getattr(settings, 'RECAPTCHA_PUBLIC_KEY', None)

    if not site_key:
        site_key = getattr(settings, 'GOOGLE_RECAPTCHA_SITE_KEY', None)

    # For local development, use test key
    if not site_key and getattr(settings, 'DEBUG', False):
        site_key = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'

    # Don't print in production to avoid log clutter
    if getattr(settings, 'DEBUG', False):
        print(f"reCAPTCHA Site Key: {'Loaded' if site_key else 'NOT SET'}")

    return {
        'RECAPTCHA_SITE_KEY': site_key,
        'RECAPTCHA_PUBLIC_KEY': site_key,
        'RECAPTCHA_KEY': site_key,
    }