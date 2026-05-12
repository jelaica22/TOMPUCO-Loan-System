from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Staff Monitoring
    path('staff-applications/', views.staff_applications, name='staff_applications'),
    path('staff-loans/', views.staff_loans, name='staff_loans'),
    path('staff-payments/', views.staff_payments, name='staff_payments'),

    # Manager Actions
    path('pending-approvals/', views.pending_approvals, name='pending_approvals'),
    path('approved-applications/', views.approved_applications, name='approved_applications'),

    # Reports & Analytics
    path('reports/', views.reports, name='reports'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),

    # Profile & 2FA
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('profile/disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('profile/generate-backup-codes/', views.generate_backup_codes, name='generate_backup_codes'),

    # 2FA Verification
    path('verify-2fa/', views.verify_2fa, name='verify_2fa'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/<int:notif_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # Application Details
    path('applications/<int:app_id>/detail/', views.application_detail, name='application_detail'),
    path('applications/<int:app_id>/review/', views.review_application, name='review_application'),
    path('applications/<int:app_id>/approve/', views.approve_application, name='approve_application'),

    # Loan Details - ADD THESE TWO LINES
    path('loans/<int:loan_id>/detail/', views.loan_detail, name='loan_detail'),
    path('loans/<int:loan_id>/payments/', views.loan_payments, name='loan_payments'),

    # Add these to your existing urlpatterns
    path('payments/<int:payment_id>/detail/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('api/application/<int:app_id>/', views.application_api_detail, name='application_api_detail'),
    path('api/application/<int:app_id>/delete/', views.delete_approved_application, name='delete_approved_application'),
]