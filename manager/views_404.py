# Add to manager/views.py - custom 404 redirect
def custom_404(request, exception=None):
    return redirect('/manager/dashboard/')
