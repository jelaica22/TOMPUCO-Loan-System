from django.db import connection


def member_profile(request):
    """Add member profile to context if user is a member"""
    context = {}

    if request.user.is_authenticated:
        try:
            # Check if the user has a member profile
            if hasattr(request.user, 'member_profile'):
                member = request.user.member_profile
                context['member'] = member

                # Safely get attributes with fallback
                try:
                    context['civil_status'] = member.civil_status
                except:
                    context['civil_status'] = None

                try:
                    context['nickname'] = member.nickname
                except:
                    context['nickname'] = None

                try:
                    context['middle_initial'] = member.middle_initial
                except:
                    context['middle_initial'] = None
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