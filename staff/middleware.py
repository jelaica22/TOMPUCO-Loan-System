from django.shortcuts import redirect


class StaffMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if path starts with /staff/
        if request.path.startswith('/staff/'):
            # Skip login page to avoid redirect loop
            if request.path == '/staff/login/':
                return self.get_response(request)

            if not request.user.is_authenticated:
                return redirect('/staff/login/')

            if not hasattr(request.user, 'staff_profile'):
                return redirect('/staff/login/')

        return self.get_response(request)