# admin_panel/context_processors.py

from .models import AdminProfile

def admin_profile(request):
    if request.user.is_authenticated:
        try:
            profile = AdminProfile.objects.get(user=request.user)
            return {'admin_profile': profile}
        except AdminProfile.DoesNotExist:
            return {'admin_profile': None}
    return {'admin_profile': None}