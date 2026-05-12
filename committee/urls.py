from django.urls import path
from . import views

app_name = 'committee'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Applications
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<int:app_id>/review/', views.review_application, name='review_application'),
    path('applications/<int:app_id>/detail/', views.application_detail, name='application_detail'),

    # History
    path('history/', views.decision_history, name='history'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/api/<str:report_type>/', views.report_api, name='report_api'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/api/count/', views.notification_count_api, name='notification_count_api'),
    path('notifications/mark-read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/logout-all-devices/', views.logout_all_devices, name='logout_all_devices'),

    # Auth - This matches the form action in base_committee.html
    path('logout/', views.committee_logout, name='custom_logout'),
]