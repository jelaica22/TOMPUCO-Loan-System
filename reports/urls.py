# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report 1: Member Loan Statement
    path('member-statement/<int:member_id>/', views.member_loan_statement, name='member_loan_statement'),
    path('member-statement/<int:member_id>/pdf/', views.member_loan_statement_pdf, name='member_loan_statement_pdf'),

    # Report 2: Monthly Summary
    path('monthly-summary/', views.monthly_summary, name='monthly_summary'),
    path('monthly-summary/pdf/', views.monthly_summary_pdf, name='monthly_summary_pdf'),
    path('monthly-summary/excel/', views.monthly_summary_excel, name='monthly_summary_excel'),

    # Report 3: Aging Report
    path('aging-report/', views.aging_report, name='aging_report'),
    path('aging-report/pdf/', views.aging_report_pdf, name='aging_report_pdf'),
    path('aging-report/excel/', views.aging_report_excel, name='aging_report_excel'),

    # Report 4: Collection Report
    path('collection-report/', views.collection_report, name='collection_report'),
    path('collection-report/pdf/', views.collection_report_pdf, name='collection_report_pdf'),
    path('collection-report/print/', views.collection_report_print, name='collection_report_print'),

    # Report 5: Penalty Report
    path('penalty-report/', views.penalty_report, name='penalty_report'),
    path('penalty-report/pdf/', views.penalty_report_pdf, name='penalty_report_pdf'),
    path('penalty-report/excel/', views.penalty_report_excel, name='penalty_report_excel'),

    # Report 6: Product Performance
    path('product-performance/', views.product_performance, name='product_performance'),
    path('product-performance/pdf/', views.product_performance_pdf, name='product_performance_pdf'),
    path('product-performance/excel/', views.product_performance_excel, name='product_performance_excel'),

    # Report 7: Approved Line Report
    path('approved-line-report/', views.approved_line_report, name='approved_line_report'),
    path('approved-line-report/pdf/', views.approved_line_report_pdf, name='approved_line_report_pdf'),
    path('approved-line-report/excel/', views.approved_line_report_excel, name='approved_line_report_excel'),
]