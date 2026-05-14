from django.shortcuts import redirect
from django.urls import reverse


class VerificationMiddleware:
    """Middleware to restrict unverified members"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip middleware for these paths to avoid redirect loops
        skip_paths = [
            '/login/',
            '/logout/',
            '/static/',
            '/media/',
            '/admin/',
            '/verification-pending/',
            '/verification-rejected/',
            '/account-suspended/',
            '/dashboard/redirect/',
        ]

        # Always skip for these paths
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)

        if request.user.is_authenticated:
            # Skip for admin/staff
            if request.user.is_staff or request.user.is_superuser:
                return self.get_response(request)

            # Check for member profile
            if hasattr(request.user, 'member_profile'):
                member = request.user.member_profile

                # Restrict unverified members
                if member.verification_status == 'pending':
                    return redirect('/verification-pending/')

                elif member.verification_status == 'rejected':
                    return redirect('/verification-rejected/')

                elif member.verification_status == 'suspended':
                    return redirect('/account-suspended/')
            else:
                # User is authenticated but has no member profile (could be staff)
                # Let them through to avoid redirect loops
                pass

        return self.get_response(request)


class RedirectManagerMiddleware:
    """Redirect managers from superadmin to manager portal"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for these paths
        skip_paths = ['/login/', '/logout/', '/static/', '/media/', '/admin/', '/dashboard/redirect/']
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)

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