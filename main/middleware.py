# main/middleware.py

from django.shortcuts import redirect
from django.urls import reverse


class VerificationMiddleware:
    """Middleware to restrict unverified members"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Skip for admin/staff
            if request.user.is_staff or request.user.is_superuser:
                return self.get_response(request)

            # Skip these paths
            skip_paths = [
                '/verification-pending/',
                '/logout/',
                '/static/',
                '/media/',
                '/admin/',
            ]

            for path in skip_paths:
                if request.path.startswith(path):
                    return self.get_response(request)

            # Check for member profile
            if hasattr(request.user, 'member_profile'):
                member = request.user.member_profile

                # Restrict unverified members - Use direct URL path
                if member.verification_status == 'pending':
                    return redirect('/verification-pending/')

                elif member.verification_status == 'rejected':
                    return redirect('/verification-rejected/')

                elif member.verification_status == 'suspended':
                    return redirect('/account-suspended/')

        return self.get_response(request)


class RedirectManagerMiddleware:
    """Redirect managers from superadmin to manager portal"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                from main.models import StaffProfile
                profile = StaffProfile.objects.get(user=request.user)
                if hasattr(profile, 'position') and profile.position.lower() == 'manager':
                    # If manager tries to access superadmin, redirect to manager dashboard
                    if request.path.startswith('/superadmin/'):
                        return redirect('/manager/dashboard/')
            except:
                pass

        response = self.get_response(request)
        return response