from django.urls import path
from . import views

app_name = 'cashier'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='dashboard'),
    path('login/', views.cashier_login, name='login'),
    path('activity/api/', views.activity_api, name='activity_api'),
    path('dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats'),
    path('post-payment/', views.post_payment, name='post_payment'),
    path('post-payment/submit/', views.post_payment_submit, name='post_payment_submit'),
    path('today-collection/', views.today_collection, name='today_collection'),
    path('end-of-day/', views.end_of_day, name='end_of_day'),
    path('api/search-payment-instruction/', views.search_payment_instruction, name='search_payment_instruction'),
    path('dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),

    # Profile URLs
    path('profile/', views.profile, name='profile'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/remove-avatar/', views.remove_avatar, name='remove_avatar'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/logout-all/', views.logout_all_devices, name='logout_all_devices'),

    # Notification URLs
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('notifications/mark-read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]