# reports/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import calendar
import csv

from main.models import Member, Loan, Payment, LoanProduct, LoanApplication, PaymentSchedule
from main.decorators import staff_required, manager_required


# ============================================================
# REPORT 1: Member Loan Statement (Individual)
# ============================================================
@login_required
def member_loan_statement(request, member_id):
    """View individual member loan statement"""
    member = get_object_or_404(Member, id=member_id)

    # Check permission
    if not (request.user.is_staff or request.user.is_superuser or
            (hasattr(request.user, 'member_profile') and request.user.member_profile == member)):
        return HttpResponse("Access Denied", status=403)

    loans = Loan.objects.filter(borrower=member)
    payments = Payment.objects.filter(member=member).order_by('-payment_date')

    context = {
        'member': member,
        'loans': loans,
        'payments': payments,
        'total_borrowed': loans.aggregate(total=Sum('principal_amount'))['total'] or 0,
        'total_paid': payments.aggregate(total=Sum('amount'))['total'] or 0,
        'total_balance': loans.aggregate(total=Sum('remaining_balance'))['total'] or 0,
        'generated_date': timezone.now(),
    }
    return render(request, 'reports/member_loan_statement_print.html', context)


@login_required
def member_loan_statement_pdf(request, member_id):
    """PDF version - simplified for now"""
    return HttpResponse("PDF Generation - Coming Soon")


# ============================================================
# REPORT 2: Monthly Summary (By Loan Type)
# ============================================================
@staff_required
def monthly_summary(request):
    """Monthly summary report by loan type"""
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    loans = Loan.objects.filter(disbursement_date__year=year, disbursement_date__month=month)

    summary = []
    for product in LoanProduct.objects.all():
        product_loans = loans.filter(loan_product=product)
        principal = product_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
        interest = product_loans.aggregate(total=Sum('total_interest'))['total'] or 0
        penalty = product_loans.aggregate(total=Sum('total_penalty_incurred'))['total'] or 0

        summary.append({
            'product': product,
            'principal': principal,
            'interest': interest,
            'penalty': penalty,
            'total': principal + interest + penalty,
            'count': product_loans.count(),
        })

    total_principal = sum(s['principal'] for s in summary)
    total_interest = sum(s['interest'] for s in summary)
    total_penalty = sum(s['penalty'] for s in summary)

    context = {
        'summary': summary,
        'total_principal': total_principal,
        'total_interest': total_interest,
        'total_penalty': total_penalty,
        'grand_total': total_principal + total_interest + total_penalty,
        'year': int(year),
        'month': int(month),
        'month_name': calendar.month_name[int(month)],
        'years': range(2020, timezone.now().year + 1),
    }
    return render(request, 'reports/monthly_summary.html', context)


@staff_required
def monthly_summary_pdf(request):
    """PDF export - simplified"""
    return HttpResponse("PDF Export - Coming Soon")


@staff_required
def monthly_summary_excel(request):
    """Excel export"""
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="monthly_summary_{year}_{month}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Loan Type', 'Number of Loans', 'Principal Amount', 'Interest', 'Penalty', 'Total'])

    loans = Loan.objects.filter(disbursement_date__year=year, disbursement_date__month=month)

    for product in LoanProduct.objects.all():
        product_loans = loans.filter(loan_product=product)
        principal = product_loans.aggregate(total=Sum('principal_amount'))['total'] or 0
        interest = product_loans.aggregate(total=Sum('total_interest'))['total'] or 0
        penalty = product_loans.aggregate(total=Sum('total_penalty_incurred'))['total'] or 0

        writer.writerow([
            product.display_name,
            product_loans.count(),
            principal,
            interest,
            penalty,
            principal + interest + penalty,
        ])

    return response


# ============================================================
# REPORT 3: Aging Report (Current vs Past Due)
# ============================================================
@staff_required
def aging_report(request):
    """Aging report - Current vs Past Due"""
    today = timezone.now().date()

    aging_data = []
    for product in LoanProduct.objects.all():
        product_loans = Loan.objects.filter(loan_product=product, status='active')

        current_loans = product_loans.filter(due_date__gte=today)
        current_amount = current_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0

        past_due_loans = product_loans.filter(due_date__lt=today)
        past_due_amount = past_due_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0

        aging_data.append({
            'product': product,
            'current_count': current_loans.count(),
            'current_amount': current_amount,
            'past_due_count': past_due_loans.count(),
            'past_due_amount': past_due_amount,
            'total_count': product_loans.count(),
            'total_amount': current_amount + past_due_amount,
        })

    context = {
        'aging_data': aging_data,
        'generated_date': today,
        'total_current_count': sum(d['current_count'] for d in aging_data),
        'total_current_amount': sum(d['current_amount'] for d in aging_data),
        'total_past_due_count': sum(d['past_due_count'] for d in aging_data),
        'total_past_due_amount': sum(d['past_due_amount'] for d in aging_data),
    }
    return render(request, 'reports/aging_report.html', context)


@staff_required
def aging_report_pdf(request):
    """PDF export - simplified"""
    return HttpResponse("PDF Export - Coming Soon")


@staff_required
def aging_report_excel(request):
    """Excel export"""
    today = timezone.now().date()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="aging_report.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ['Loan Type', '# Current', 'Amount Current', '# Past Due', 'Amount Past Due', '# Total', 'Total Amount'])

    for product in LoanProduct.objects.all():
        product_loans = Loan.objects.filter(loan_product=product, status='active')
        current_loans = product_loans.filter(due_date__gte=today)
        past_due_loans = product_loans.filter(due_date__lt=today)

        writer.writerow([
            product.display_name,
            current_loans.count(),
            f"{current_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0}",
            past_due_loans.count(),
            f"{past_due_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0}",
            product_loans.count(),
            f"{product_loans.aggregate(total=Sum('remaining_balance'))['total'] or 0}",
        ])

    return response


# ============================================================
# REPORT 4: Collection Report (Daily/Weekly/Monthly)
# ============================================================
@staff_required
def collection_report(request):
    """Collection report"""
    period = request.GET.get('period', 'daily')
    date_filter = request.GET.get('date')

    if date_filter:
        date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
    else:
        date_filter = timezone.now().date()

    if period == 'daily':
        payments = Payment.objects.filter(payment_date=date_filter, status='completed')
        title = f"Daily Collection Report - {date_filter.strftime('%B %d, %Y')}"
    elif period == 'weekly':
        start_date = date_filter - timedelta(days=date_filter.weekday())
        end_date = start_date + timedelta(days=6)
        payments = Payment.objects.filter(payment_date__range=[start_date, end_date], status='completed')
        title = f"Weekly Collection Report - {start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}"
    else:
        payments = Payment.objects.filter(payment_date__year=date_filter.year, payment_date__month=date_filter.month,
                                          status='completed')
        title = f"Monthly Collection Report - {date_filter.strftime('%B %Y')}"

    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'title': title,
        'payments': payments,
        'total_amount': total_amount,
        'total_count': payments.count(),
        'period': period,
        'selected_date': date_filter,
    }
    return render(request, 'reports/collection_report.html', context)


@staff_required
def collection_report_pdf(request):
    """PDF export - simplified"""
    return HttpResponse("PDF Export - Coming Soon")


@staff_required
def collection_report_print(request):
    """Print-friendly version"""
    period = request.GET.get('period', 'daily')
    date_filter = request.GET.get('date')

    if date_filter:
        date_filter = datetime.strptime(date_filter, '%Y-%m-%d').date()
    else:
        date_filter = timezone.now().date()

    if period == 'daily':
        payments = Payment.objects.filter(payment_date=date_filter, status='completed')
    elif period == 'weekly':
        start_date = date_filter - timedelta(days=date_filter.weekday())
        end_date = start_date + timedelta(days=6)
        payments = Payment.objects.filter(payment_date__range=[start_date, end_date], status='completed')
    else:
        payments = Payment.objects.filter(payment_date__year=date_filter.year, payment_date__month=date_filter.month,
                                          status='completed')

    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'payments': payments,
        'total_amount': total_amount,
        'total_count': payments.count(),
        'generated_date': timezone.now(),
    }
    return render(request, 'reports/collection_report_print.html', context)


# ============================================================
# REPORT 5: Penalty Report
# ============================================================
@staff_required
def penalty_report(request):
    """Report of loans with penalties"""
    loans_with_penalty = []

    for loan in Loan.objects.filter(status='active'):
        if loan.total_penalty_incurred > 0:
            days_overdue = 0
            if loan.due_date < timezone.now().date():
                days_overdue = (timezone.now().date() - loan.due_date).days

            loans_with_penalty.append({
                'loan': loan,
                'member': loan.borrower,
                'days_overdue': days_overdue,
                'remaining_balance': loan.remaining_balance,
                'penalty_amount': loan.total_penalty_incurred,
            })

    total_penalty = sum(l['penalty_amount'] for l in loans_with_penalty)

    context = {
        'loans': loans_with_penalty,
        'total_penalty': total_penalty,
        'total_count': len(loans_with_penalty),
        'generated_date': timezone.now(),
    }
    return render(request, 'reports/penalty_report.html', context)


@staff_required
def penalty_report_pdf(request):
    """PDF export - simplified"""
    return HttpResponse("PDF Export - Coming Soon")


@staff_required
def penalty_report_excel(request):
    """Excel export"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="penalty_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Loan Number', 'Member Name', 'Days Overdue', 'Remaining Balance', 'Penalty Amount'])

    for loan in Loan.objects.filter(status='active', total_penalty_incurred__gt=0):
        days_overdue = 0
        if loan.due_date < timezone.now().date():
            days_overdue = (timezone.now().date() - loan.due_date).days

        writer.writerow([
            loan.loan_number,
            f"{loan.borrower.last_name}, {loan.borrower.first_name}",
            days_overdue,
            loan.remaining_balance,
            loan.total_penalty_incurred,
        ])

    return response


# ============================================================
# REPORT 6: Loan Product Performance
# ============================================================
@manager_required
def product_performance(request):
    """Loan product performance report"""
    performance = []

    for product in LoanProduct.objects.all():
        applications = LoanApplication.objects.filter(loan_product=product)
        approved_apps = applications.filter(status='manager_approved')
        loans = Loan.objects.filter(loan_product=product)
        active_loans = loans.filter(status='active')
        defaulted = loans.filter(status='defaulted')

        default_rate = (defaulted.count() / loans.count() * 100) if loans.count() > 0 else 0

        performance.append({
            'product': product,
            'applications': applications.count(),
            'approved': approved_apps.count(),
            'disbursed': loans.count(),
            'active': active_loans.count(),
            'defaulted': defaulted.count(),
            'default_rate': default_rate,
            'total_amount': loans.aggregate(total=Sum('principal_amount'))['total'] or 0,
        })

    context = {
        'performance': performance,
        'generated_date': timezone.now(),
        'total_applications': sum(p['applications'] for p in performance),
        'total_disbursed': sum(p['disbursed'] for p in performance),
        'total_amount': sum(p['total_amount'] for p in performance),
    }
    return render(request, 'reports/product_performance.html', context)


@manager_required
def product_performance_pdf(request):
    """PDF export - simplified"""
    return HttpResponse("PDF Export - Coming Soon")


@manager_required
def product_performance_excel(request):
    """Excel export"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="product_performance.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ['Product', 'Applications', 'Approved', 'Disbursed', 'Active', 'Defaulted', 'Default Rate', 'Total Amount'])

    for product in LoanProduct.objects.all():
        applications = LoanApplication.objects.filter(loan_product=product)
        approved_apps = applications.filter(status='manager_approved')
        loans = Loan.objects.filter(loan_product=product)
        defaulted = loans.filter(status='defaulted')
        default_rate = (defaulted.count() / loans.count() * 100) if loans.count() > 0 else 0

        writer.writerow([
            product.display_name,
            applications.count(),
            approved_apps.count(),
            loans.count(),
            loans.filter(status='active').count(),
            defaulted.count(),
            f"{default_rate:.1f}%",
            loans.aggregate(total=Sum('principal_amount'))['total'] or 0,
        ])

    return response


# ============================================================
# REPORT 7: Approved Line Report
# ============================================================
@manager_required
def approved_line_report(request):
    """Report of approved loan lines"""
    applications = LoanApplication.objects.filter(
        approved_line__isnull=False,
        committee_approved_date__isnull=False
    ).order_by('-committee_approved_date')

    total_requested = applications.aggregate(total=Sum('requested_amount'))['total'] or 0
    total_approved = applications.aggregate(total=Sum('approved_line'))['total'] or 0
    reduction_amount = total_requested - total_approved
    reduction_percent = (reduction_amount / total_requested * 100) if total_requested > 0 else 0

    context = {
        'applications': applications,
        'total_requested': total_requested,
        'total_approved': total_approved,
        'reduction_amount': reduction_amount,
        'reduction_percent': reduction_percent,
        'total_count': applications.count(),
        'generated_date': timezone.now(),
    }
    return render(request, 'reports/approved_line_report.html', context)


@manager_required
def approved_line_report_pdf(request):
    """PDF export - simplified"""
    return HttpResponse("PDF Export - Coming Soon")


@manager_required
def approved_line_report_excel(request):
    """Excel export"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="approved_line_report.csv"'

    writer = csv.writer(response)
    writer.writerow(
        ['Application ID', 'Member Name', 'Requested Amount', 'Approved Line', 'Reduction Reason', 'Date Approved'])

    for app in LoanApplication.objects.filter(approved_line__isnull=False, committee_approved_date__isnull=False):
        writer.writerow([
            app.application_id,
            f"{app.member.last_name}, {app.member.first_name}",
            app.requested_amount,
            app.approved_line,
            app.committee_reduction_reason or 'N/A',
            app.committee_approved_date.strftime('%Y-%m-%d'),
        ])

    return response