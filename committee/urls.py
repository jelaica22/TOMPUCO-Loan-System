from django.urls import path
from . import views

app_name = 'committee'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('applications/', views.applications_list, name='applications_list'),
    path('applications/<int:app_id>/review/', views.review_application, name='review_application'),
    path('applications/<int:app_id>/detail/', views.application_detail, name='application_detail'),
    path('history/', views.decision_history, name='history'),
    path('reports/', views.reports, name='reports'),
    path('reports/api/<str:report_type>/', views.report_api, name='report_api'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notif_id>/', views.notification_detail, name='notification_detail'),
    path('notifications/api/count/', views.notification_count_api, name='notification_count_api'),
    # path('notifications/api/list/', views.notification_list_api, name='notification_list_api'),  # ADD THIS
    path('notifications/mark-read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('profile/', views.profile, name='profile'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/logout-all-devices/', views.logout_all_devices, name='logout_all_devices'),
    path('logout/', views.committee_logout, name='custom_logout'),
    path('vote/<int:app_id>/', views.cast_vote, name='cast_vote'),  # ADD THIS
]
