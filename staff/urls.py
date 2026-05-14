# staff/urls.py
from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='index'),

    # Applications
    path('applications/', views.applications_list, name='staff_applications'),
    path('applications/create/', views.create_application, name='create_application'),
    path('applications/<int:pk>/', views.application_review, name='review_application'),
    path('applications/<int:pk>/edit/', views.edit_application, name='edit_application'),
    path('applications/<int:pk>/add-charges/', views.add_charges, name='add_charges'),
    path('applications/<int:app_id>/create-loan/', views.create_loan, name='create_loan'),

    # Loans (Loan Register)
    path('loans/', views.loan_list, name='staff_loans'),
    path('loans/<int:pk>/', views.loan_detail, name='loan_detail'),
    path('loans/<int:pk>/schedule/', views.loan_payment_schedule, name='loan_payment_schedule'),
    path('loans/<int:pk>/restructure/', views.process_restructuring, name='process_restructuring'),
    path('loans/export/', views.export_loans, name='export_loans'),

    # Payments
    path('payments/', views.payment_list, name='staff_payments'),
    path('payments/issue/', views.issue_payment_instruction, name='issue_payment_instruction'),
    path('payments/history/', views.payment_history, name='payment_history'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/receipt/', views.payment_receipt_json, name='payment_receipt_json'),

    # Restructuring
    path('restructuring/', views.restructuring_list, name='restructuring_list'),
    path('restructuring/<int:pk>/', views.restructuring_detail, name='restructuring_detail'),
    path('restructuring/request/', views.restructuring_request_form, name='restructuring_request'),
    path('restructuring/request/<int:member_id>/', views.restructuring_request_form, name='restructuring_request_form'),
    path('api/restructuring/request/', views.restructuring_api_request, name='restructuring_api_request'),
    path('api/restructuring/list/', views.restructuring_api_list, name='restructuring_api_list'),
    path('api/restructuring/<int:pk>/', views.restructuring_api_detail, name='restructuring_api_detail'),

    # Reports
    path('reports/', views.reports_index, name='staff_reports'),
    path('reports/loan-summary/', views.report_loan_summary, name='report_loan_summary'),
    path('reports/collection/', views.report_collection, name='report_collection'),
    path('reports/aging/', views.report_aging, name='report_aging'),
    path('reports/member/', views.report_member, name='report_member'),
    path('reports/loan-product/', views.report_loan_product, name='report_loan_product'),
    path('reports/restructuring/', views.report_restructuring, name='report_restructuring'),
    path('reports/penalty/', views.report_penalty, name='report_penalty'),
    path('reports/export/excel/', views.export_report_excel, name='export_report_excel'),
    path('reports/export/pdf/', views.export_report_pdf, name='export_report_pdf'),

    # Report API endpoints
    path('reports/loan-summary/api/', views.report_loan_summary_api, name='report_loan_summary_api'),
    path('reports/collection/api/', views.report_collection_api, name='report_collection_api'),
    path('reports/aging/api/', views.report_aging_api, name='report_aging_api'),
    path('reports/member/api/', views.report_member_api, name='report_member_api'),
    path('reports/loan-product/api/', views.report_loan_product_api, name='report_loan_product_api'),
    path('reports/restructuring/api/', views.report_restructuring_api, name='report_restructuring_api'),
    path('reports/penalty/api/', views.report_penalty_api, name='report_penalty_api'),

    # Notifications
    path('notifications/', views.notifications_page, name='notifications_page'),
    path('notifications/api/', views.notifications_api, name='notifications_api'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),

    # Profile
    path('profile/', views.staff_profile_view, name='staff_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/logout-all/', views.logout_all_devices, name='logout_all_devices'),

    # 2FA URLs
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('2fa/disable/', views.disable_2fa, name='disable_2fa'),
    path('2fa/backup-codes/', views.generate_backup_codes, name='generate_backup_codes'),
    path('2fa/verify/', views.verify_2fa_login, name='verify_2fa'),

    # API endpoints
    path('api/application/<int:pk>/', views.application_api, name='application_api'),
    path('api/bulk-forward/', views.bulk_forward, name='bulk_forward'),
    path('api/bulk-reject/', views.bulk_reject, name='bulk_reject'),
    path('api/member-search/', views.member_search, name='member_search'),
    path('api/loan-status/<int:loan_id>/', views.loan_status_api, name='loan_status_api'),
    path('api/calculate-payment/', views.calculate_payment_breakdown, name='calculate_payment_breakdown'),
    path('api/co-maker-validate/', views.validate_co_maker, name='validate_co_maker'),
    path('api/issue-instruction/', views.issue_instruction_api, name='issue_instruction_api'),

    # Add these to your staff/urls.py
    path('api/application/<int:pk>/', views.application_api, name='application_api'),
    path('api/loan-status/<int:loan_id>/', views.loan_status_api, name='loan_status_api'),

    # Logout
    path('logout/', views.staff_logout, name='logout'),
]
