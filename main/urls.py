# main/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views
from . import notification_views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'main'

urlpatterns = [
    # Main URLs
    path('', views.landing_page, name='landing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Password Reset URLs (FIXED)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='main/password_reset.html',
             email_template_name='main/password_reset_email.html',
             subject_template_name='main/password_reset_subject.txt',
             success_url=reverse_lazy('main:password_reset_done')
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='main/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='main/password_reset_confirm.html',
             success_url=reverse_lazy('main:password_reset_complete')
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='main/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    # Member Profile URLs
    path('profile/', views.member_profile, name='member_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/upload-id/', views.upload_valid_id, name='upload_valid_id'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('my-qr-code/', views.member_qr_code, name='member_qr'),

    # 2FA URLs for Members
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('2fa/backup-codes/', views.generate_backup_codes, name='generate_backup_codes'),
    path('2fa/verify/', views.verify_2fa_login, name='verify_2fa'),

    # Member application
    path('api/member-applications/', views.member_applications_api, name='member_applications_api'),
    path('api/member-loans/', views.member_loans_api, name='member_loans_api'),
    path('api/member-payments/', views.member_payments_api, name='member_payments_api'),

    # Loan Application URLs
    path('apply-loan/', views.apply_loan, name='apply_loan'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:app_id>/', views.view_application_details, name='view_application_details'),

    # Loan URLs
    path('my-loans/', views.my_loans, name='my_loans'),
    path('loan/<int:loan_id>/schedule/', views.payment_schedule, name='payment_schedule'),

    # Payment URLs
    path('payment-history/', views.payment_history, name='payment_history'),
    path('receipt/<int:payment_id>/download/', views.download_receipt, name='download_receipt'),

    # API URLs
    path('api/co-maker/search/', views.search_co_maker, name='search_co_maker'),
    path('api/co-maker/<int:co_maker_id>/validate/', views.validate_co_maker, name='validate_co_maker'),
    path('api/save-signature/', views.save_signature, name='save_signature'),
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    path('api/submit-application/', views.submit_loan_application, name='submit_loan_application'),
    path('api/upload-collateral/<int:application_id>/', views.upload_collateral, name='upload_collateral'),
    path('api/loan-status/', views.member_loan_status, name='member_loan_status'),

    # Loan Product
    path('loan-types/', views.loan_types, name='loan_types'),

    # Payment Schedule
    path('api/loan/<int:loan_id>/schedule/', views.loan_payment_schedule_api, name='loan_payment_schedule_api'),

    # Analytics
    path('api/member-analytics/', views.member_analytics_api, name='member_analytics_api'),
    path('api/member-stats/', views.member_stats_api, name='member_stats_api'),

    # Chatbot API
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),

    # Notification API URLs
    path('api/notifications/', views.get_notifications_api, name='get_notifications'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Notifications
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('notifications/', views.notifications_page, name='get_notifications'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/notifications/read-all/', views.mark_all_notifications_read_api, name='mark_all_notifications_read_api'),
    path('api/notifications/<int:notif_id>/delete/', views.delete_notification_api, name='delete_notification_api'),

    # Shared Notification URLs
    path('notifications/api/', notification_views.get_notifications_api, name='get_notifications_api'),
    path('notifications/<int:notification_id>/read/', notification_views.mark_notification_read,
         name='mark_notification_read'),
    path('notifications/read-all/', notification_views.mark_all_notifications_read, name='mark_all_notifications_read'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)