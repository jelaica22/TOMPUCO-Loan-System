from staff.models import StaffProfile
from .models import Member
from django.contrib.auth.models import User

def staff_profile_context(request):
    if request.user.is_authenticated:
        try:
            profile = StaffProfile.objects.get(user=request.user)
            return {'staff_profile': profile}
        except StaffProfile.DoesNotExist:
            return {}
    return {}



def member_profile(request):
    """Make member profile available to all templates"""
    if request.user.is_authenticated:
        try:
            member = Member.objects.get(user=request.user)
            return {'member_profile': member}
        except Member.DoesNotExist:
            return {'member_profile': None}
    return {'member_profile': None}