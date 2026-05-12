# manager/context_processors.py

from .models import ManagerProfile

def manager_profile(request):
    """Make manager profile available to all templates"""
    if request.user.is_authenticated:
        try:
            profile = ManagerProfile.objects.get(user=request.user)
            return {'manager_profile': profile}
        except ManagerProfile.DoesNotExist:
            return {'manager_profile': None}
    return {'manager_profile': None}