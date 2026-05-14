def cashier_profile(request):
    context = {}

    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'staff_profile'):
                profile = request.user.staff_profile
                if hasattr(profile, 'position') and profile.position == 'cashier':
                    context['is_cashier'] = True
                    context['cashier_profile'] = profile
        except Exception as e:
            print(f"Cashier profile error: {e}")

    return context