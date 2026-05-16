from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/activity/', views.api_activity_feed, name='api_activity_feed'),
    path('member/<int:member_id>/verify/', views.verify_member, name='verify_member'),
    path('create-staff-user/', views.create_staff_user, name='create_staff_user'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('loan-applications/<int:app_id>/process/', views.loan_application_process, name='loan_application_process'),

    # Users Management
    path('users/', views.users_list, name='users_list'),
    path('users/list/', views.users_list, name='user_list'),  # Alias
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/add/', views.user_create, name='user_create'),

    # Members Management
    path('members/', views.members_list, name='members_list'),
    path('members/create/', views.member_create, name='member_create'),
    path('members/<int:member_id>/', views.member_detail, name='member_detail'),
    path('members/<int:member_id>/edit/', views.member_edit, name='member_edit'),
    path('members/<int:member_id>/delete/', views.member_delete, name='member_delete'),

    # Loan Products
    path('loan-products/', views.loan_products_list, name='loan_products_list'),
    path('loan-products/create/', views.loan_product_create, name='loan_product_create'),
    path('loan-products/<int:product_id>/', views.loan_product_detail, name='loan_product_detail'),
    path('loan-products/<int:product_id>/edit/', views.loan_product_edit, name='loan_product_edit'),
    path('loan-products/<int:product_id>/delete/', views.loan_product_delete, name='loan_product_delete'),

    # Loan Applications
    path('loan-applications/', views.loan_applications_list, name='loan_applications_list'),
    path('loan-applications/create/', views.loan_application_create, name='loan_application_create'),
    path('loan-applications/<int:app_id>/', views.loan_application_detail, name='loan_application_detail'),
    path('loan-applications/<int:app_id>/edit/', views.loan_application_edit, name='loan_application_edit'),
    path('loan-applications/<int:app_id>/delete/', views.loan_application_delete, name='loan_application_delete'),

    # Loans
    path('loans/', views.loans_list, name='loans_list'),
    path('loans/create/', views.loan_create, name='loan_create'),
    path('loans/<int:loan_id>/', views.loan_detail, name='loan_detail'),
    path('loans/<int:loan_id>/edit/', views.loan_edit, name='loan_edit'),

    # Payment Schedules
    path('payment-schedules/', views.payment_schedules_list, name='payment_schedules_list'),
    path('payment-schedules/generate/', views.payment_schedule_generate, name='payment_schedule_generate'),
    path('payment-schedules/<int:schedule_id>/', views.payment_schedule_detail, name='payment_schedule_detail'),
    path('payment-schedules/<int:schedule_id>/edit/', views.payment_schedule_edit, name='payment_schedule_edit'),
    path('payment-schedules/<int:schedule_id>/mark-paid/', views.payment_schedule_mark_paid,
         name='payment_schedule_mark_paid'),
    path('payment-schedules/<int:schedule_id>/delete/', views.payment_schedule_delete, name='payment_schedule_delete'),

    # Payments
    path('payments/', views.payments_list, name='payments_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:payment_id>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:payment_id>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('payments/<int:payment_id>/delete/', views.payment_delete, name='payment_delete'),

    # Payment Receipts
    path('payment-receipts/', views.payment_receipts_list, name='payment_receipts_list'),

    # Member Documents
    path('member-documents/', views.member_documents_list, name='member_documents_list'),
    path('member-documents/create/', views.member_document_create, name='member_document_create'),
    path('member-documents/<int:doc_id>/verify/', views.member_document_verify, name='member_document_verify'),
    path('member-documents/<int:doc_id>/delete/', views.member_document_delete, name='member_document_delete'),
    path('members/<int:member_id>/verify/', views.verify_member_ajax, name='verify_member_ajax'),

    # Loan Attachments
    path('loan-attachments/', views.loan_attachments_list, name='loan_attachments_list'),
    path('loan-attachments/create/', views.loan_attachment_create, name='loan_attachment_create'),
    path('loan-attachments/<int:att_id>/', views.loan_attachment_detail, name='loan_attachment_detail'),
    path('loan-attachments/<int:att_id>/delete/', views.loan_attachment_delete, name='loan_attachment_delete'),

    # Committee Decisions
    path('committee-decisions/', views.committee_decisions_list, name='committee_decisions_list'),

    # Notifications
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/<int:notif_id>/mark-read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/<int:notif_id>/delete/', views.notification_delete, name='notification_delete'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/notifications/mark-read/<int:notif_id>/', views.mark_notification_read_api, name='mark_notification_read_api'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read_api, name='mark_all_notifications_read_api'),

    # Audit Logs
    path('audit-logs/', views.audit_logs_list, name='audit_logs_list'),
    path('audit-logs/<int:log_id>/', views.audit_log_detail, name='audit_log_detail'),

    # System Settings
    path('system-settings/', views.system_settings_list, name='system_settings_list'),
    path('system-settings/<int:setting_id>/update/', views.system_setting_update, name='system_setting_update'),

    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/api/<str:report_type>/', views.reports_api, name='reports_api'),
]