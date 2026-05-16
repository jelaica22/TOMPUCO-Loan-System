# tompuco/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Cashier, Committee, Manager URLs
    path('cashier/', include('cashier.urls')),
    path('committee/', include('committee.urls')),
    path('manager/', include('manager.urls')),

    # Django admin
    path('django-admin/', admin.site.urls),

    # Super Admin Panel - MUST use namespace 'superadmin'
    path('superadmin/', include('admin_panel.urls', namespace='superadmin')),

    # Redirect /admin/ to /superadmin/
    path('admin/', lambda request: redirect('/superadmin/')),

    # Reports
    path('reports/', include('reports.urls')),

    # Member Portal
    path('', include('main.urls')),

    # Staff Portal
    path('staff/', include('staff.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)