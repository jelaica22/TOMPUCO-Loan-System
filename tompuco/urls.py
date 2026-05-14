"""
URL configuration for tompuco project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# tompuco/urls.py
"""
URL configuration for tompuco project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('cashier/', include('cashier.urls')),
    path('committee/', include('committee.urls')),
    path('manager/', include('manager.urls')),

    # Django admin (keep at different URL)
    path('django-admin/', admin.site.urls),

    # Super Admin Panel
    path('superadmin/', include('admin_panel.urls')),

    # Redirect /admin/ to /superadmin/
    path('admin/', lambda request: redirect('/superadmin/')),

    # Reports
    path('reports/', include('reports.urls')),

    # Member Portal (includes verification-pending/)
    path('', include('main.urls')),

    # Staff Portal
    path('staff/', include('staff.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)