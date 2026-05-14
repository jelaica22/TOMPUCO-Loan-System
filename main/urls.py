# main/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from . import views
from . import notification_views

app_name = 'main'

urlpatterns = [
    # ============================================================
    # AUTHENTICATION & PUBLIC URLs
    # ============================================================
    path('', views.landing_page, name='landing'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/redirect/', views.role_based_redirect, name='role_based_redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # ============================================================
    # VERIFICATION URL
    # ============================================================
    path('verification-pending/', views.verification_pending, name='verification_pending'),

    # ============================================================
    # AJAX CHECK URLs
    # ============================================================
    path('check-username/', views.check_username, name='check_username'),
    path('check-email/', views.check_email, name='check_email'),

    # ============================================================
    # PASSWORD RESET URLs
    # ============================================================
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='main/password_reset.html',
             email_template_name='main/password_reset_email.html',
             subject_template_name='main/password_reset_subject.txt',
             success_url=reverse_lazy('main:password_reset_done')
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='main/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='main/password_reset_confirm.html',
             success_url=reverse_lazy('main:password_reset_complete')
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='main/password_reset_complete.html'),
         name='password_reset_complete'),

    # ============================================================
    # PROFILE URLs
    # ============================================================
    path('profile/', views.member_profile, name='member_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/upload-id/', views.upload_valid_id, name='upload_valid_id'),
    path('upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('my-qr-code/', views.member_qr_code, name='member_qr'),

    # ============================================================
    # 2FA URLs
    # ============================================================
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('2fa/backup-codes/', views.generate_backup_codes, name='generate_backup_codes'),
    path('2fa/verify/', views.verify_2fa_login, name='verify_2fa'),

    # ============================================================
    # LOAN APPLICATION URLs
    # ============================================================
    path('apply-loan/', views.apply_loan, name='apply_loan'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:app_id>/', views.view_application_details, name='view_application_details'),

    # ============================================================
    # LOAN URLs
    # ============================================================
    path('my-loans/', views.my_loans, name='my_loans'),
    path('loan/<int:loan_id>/schedule/', views.payment_schedule, name='payment_schedule'),
    path('loan-types/', views.loan_types, name='loan_types'),

    # ============================================================
    # PAYMENT URLs
    # ============================================================
    path('payment-history/', views.payment_history, name='payment_history'),
    path('receipt/<int:payment_id>/download/', views.download_receipt, name='download_receipt'),

    # ============================================================
    # API ENDPOINTS
    # ============================================================
    # Member Data APIs
    path('api/member/applications/', views.member_applications_api, name='member_applications_api'),
    path('api/member-payments/', views.member_payments_api, name='member_payments_api'),
    path('api/member-loans/', views.member_loans_api, name='member_loans_api'),
    path('api/member-analytics/', views.member_analytics_api, name='member_analytics_api'),
    path('api/member-stats/', views.member_stats_api, name='member_stats_api'),

    # Loan APIs
    path('api/loan/<int:loan_id>/schedule/', views.loan_payment_schedule_api, name='loan_payment_schedule_api'),
    path('api/loan-status/', views.member_loan_status, name='member_loan_status'),

    # Co-maker APIs
    path('api/co-maker/search/', views.search_co_maker, name='search_co_maker'),
    path('api/co-maker/<int:co_maker_id>/validate/', views.validate_co_maker, name='validate_co_maker'),

    # Application Process APIs
    path('api/save-signature/', views.save_signature, name='save_signature'),
    path('api/send-otp/', views.send_otp, name='send_otp'),
    path('api/verify-otp/', views.verify_otp, name='verify_otp'),
    path('api/submit-application/', views.submit_loan_application, name='submit_loan_application'),
    path('api/upload-collateral/<int:application_id>/', views.upload_collateral, name='upload_collateral'),

    # Chatbot API
    path('api/chatbot/', views.chatbot_api, name='chatbot_api'),

    # Notification APIs - Consolidated (removed duplicates)
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/<int:notif_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/<int:notif_id>/delete/', views.delete_notification_api, name='delete_notification_api'),
    path('api/notifications/mark-read/<int:notif_id>/', views.mark_notification_read_api,
         name='mark_notification_read_api'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read_api,
         name='mark_all_notifications_read_api'),

    # Notification Page
    path('notifications/', views.notifications_page, name='notifications_page'),

    # Signature and OTP APIs
    path('save-signature/', views.save_signature, name='save_signature'),
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('submit-application/', views.submit_loan_application, name='submit_loan_application'),

    # Add these after your verification URL:
    path('verification-rejected/', views.verification_rejected, name='verification_rejected'),
    path('account-suspended/', views.account_suspended, name='account_suspended'),


]

# Static and Media files for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)