# cashier/context_processors.py

def cashier_profile(request):
    """Make cashier/staff profile available to all templates"""
    if request.user.is_authenticated:
        # Try to get the profile from different possible sources
        if hasattr(request.user, 'staff_profile'):
            return {'user_profile': request.user.staff_profile}
        elif hasattr(request.user, 'cashier_profile'):
            return {'user_profile': request.user.cashier_profile}
        elif hasattr(request.user, 'member_profile'):
            return {'user_profile': request.user.member_profile}
    return {'user_profile': None}