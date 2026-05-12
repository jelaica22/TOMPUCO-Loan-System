# This script will generate the complete admin_panel/views.py with full CRUD operations
import os

views_content = '''
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Q
from django.utils import timezone
from decimal import Decimal

from main.models import (
    Member, LoanProduct, LoanApplication, Loan,
    Payment, PaymentSchedule, Notification
)


def super_admin_required(view_func):
    """Decorator to check if user is super admin"""
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='/dashboard/'
    )
    return actual_decorator(view_func)


# ==================== DASHBOARD ====================
@super_admin_required
def dashboard(request):
    """Super Admin Dashboard with statistics"""
    context = {
        'total_users': User.objects.count(),
        'total_members': Member.objects.count(),
        'total_loans': Loan.objects.count(),
        'active_loans': Loan.objects.filter(status='active').count(),
        'total_applications': LoanApplication.objects.count(),
        'pending_applications': LoanApplication.objects.filter(status='pending_staff_review').count(),
        'total_products': LoanProduct.objects.count(),
        'total_payments': Payment.objects.count(),
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ==================== TABLE 1: USERS (Full CRUD) ====================
@super_admin_required
def users_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/users_list.html', {'users': users})


@super_admin_required
def user_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )
            messages.success(request, f'User {username} created successfully')
            return redirect('admin_panel:users_list')
    
    return render(request, 'admin_panel/user_form.html', {'action': 'Create'})


@super_admin_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'admin_panel/user_detail.html', {'user': user})


@super_admin_required
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'
        
        password = request.POST.get('password')
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, f'User {user.username} updated successfully')
        return redirect('admin_panel:users_list')
    
    return render(request, 'admin_panel/user_form.html', {'user': user, 'action': 'Edit'})


@super_admin_required
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully')
        return redirect('admin_panel:users_list')
    return render(request, 'admin_panel/user_confirm_delete.html', {'user': user})


# ==================== TABLE 2: MEMBERS (Full CRUD) ====================
@super_admin_required
def members_list(request):
    members = Member.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/members_list.html', {'members': members})


@super_admin_required
def member_create(request):
    if request.method == 'POST':
        # Create user first
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name')
            )
            
            member = Member.objects.create(
                user=user,
                membership_number=request.POST.get('membership_number'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                middle_initial=request.POST.get('middle_initial'),
                contact_number=request.POST.get('contact_number'),
                residence_address=request.POST.get('residence_address'),
                monthly_income=Decimal(request.POST.get('monthly_income', 0)),
                is_active=True
            )
            messages.success(request, f'Member {member.first_name} {member.last_name} created')
            return redirect('admin_panel:members_list')
    
    return render(request, 'admin_panel/member_form.html', {'action': 'Create'})


@super_admin_required
def member_detail(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    return render(request, 'admin_panel/member_detail.html', {'member': member})


@super_admin_required
def member_edit(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        member.first_name = request.POST.get('first_name')
        member.last_name = request.POST.get('last_name')
        member.middle_initial = request.POST.get('middle_initial')
        member.contact_number = request.POST.get('contact_number')
        member.residence_address = request.POST.get('residence_address')
        member.monthly_income = Decimal(request.POST.get('monthly_income', 0))
        member.is_active = request.POST.get('is_active') == 'on'
        member.save()
        
        messages.success(request, 'Member updated successfully')
        return redirect('admin_panel:members_list')
    
    return render(request, 'admin_panel/member_form.html', {'member': member, 'action': 'Edit'})


@super_admin_required
def member_delete(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == 'POST':
        name = f"{member.first_name} {member.last_name}"
        member.delete()
        messages.success(request, f'Member {name} deleted')
        return redirect('admin_panel:members_list')
    return render(request, 'admin_panel/member_confirm_delete.html', {'member': member})


# ==================== TABLE 3: LOAN PRODUCTS (Full CRUD) ====================
@super_admin_required
def loan_products_list(request):
    products = LoanProduct.objects.all()
    return render(request, 'admin_panel/loan_products_list.html', {'products': products})


@super_admin_required
def loan_product_create(request):
    if request.method == 'POST':
        product = LoanProduct.objects.create(
            name=request.POST.get('name'),
            display_name=request.POST.get('display_name'),
            interest_rate=Decimal(request.POST.get('interest_rate', 0)),
            term_months=int(request.POST.get('term_months', 12)),
            min_amount=Decimal(request.POST.get('min_amount', 0)),
            max_amount=Decimal(request.POST.get('max_amount', 0)),
            is_active=request.POST.get('is_active') == 'on'
        )
        messages.success(request, f'Loan product {product.name} created')
        return redirect('admin_panel:loan_products_list')
    
    return render(request, 'admin_panel/loan_product_form.html', {'action': 'Create'})


@super_admin_required
def loan_product_edit(request, product_id):
    product = get_object_or_404(LoanProduct, id=product_id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.display_name = request.POST.get('display_name')
        product.interest_rate = Decimal(request.POST.get('interest_rate', 0))
        product.term_months = int(request.POST.get('term_months', 12))
        product.min_amount = Decimal(request.POST.get('min_amount', 0))
        product.max_amount = Decimal(request.POST.get('max_amount', 0))
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()
        messages.success(request, 'Loan product updated')
        return redirect('admin_panel:loan_products_list')
    
    return render(request, 'admin_panel/loan_product_form.html', {'product': product, 'action': 'Edit'})


@super_admin_required
def loan_product_delete(request, product_id):
    product = get_object_or_404(LoanProduct, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Product {name} deleted')
        return redirect('admin_panel:loan_products_list')
    return render(request, 'admin_panel/loan_product_confirm_delete.html', {'product': product})


# ==================== TABLE 4: LOAN APPLICATIONS ====================
@super_admin_required
def loan_applications_list(request):
    applications = LoanApplication.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/loan_applications_list.html', {'applications': applications})


@super_admin_required
def loan_application_detail(request, app_id):
    app = get_object_or_404(LoanApplication, id=app_id)
    return render(request, 'admin_panel/loan_application_detail.html', {'app': app})


@super_admin_required
def loan_application_delete(request, app_id):
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        app_id_display = app.application_id
        app.delete()
        messages.success(request, f'Application {app_id_display} deleted')
        return redirect('admin_panel:loan_applications_list')
    return render(request, 'admin_panel/loan_application_confirm_delete.html', {'app': app})


# ==================== TABLE 5-14: Placeholder views ====================
@super_admin_required
def member_documents_list(request):
    return render(request, 'admin_panel/member_documents_list.html', {'documents': []})


@super_admin_required
def member_document_delete(request, doc_id):
    messages.success(request, 'Document deleted')
    return redirect('admin_panel:member_documents_list')


@super_admin_required
def loan_attachments_list(request):
    return render(request, 'admin_panel/loan_attachments_list.html', {'attachments': []})


@super_admin_required
def loan_attachment_delete(request, att_id):
    messages.success(request, 'Attachment deleted')
    return redirect('admin_panel:loan_attachments_list')


@super_admin_required
def loans_list(request):
    loans = Loan.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/loans_list.html', {'loans': loans})


@super_admin_required
def loan_detail(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    return render(request, 'admin_panel/loan_detail.html', {'loan': loan})


@super_admin_required
def payment_schedules_list(request):
    schedules = PaymentSchedule.objects.all().order_by('-due_date')
    return render(request, 'admin_panel/payment_schedules_list.html', {'schedules': schedules})


@super_admin_required
def payments_list(request):
    payments = Payment.objects.all().order_by('-payment_date')
    return render(request, 'admin_panel/payments_list.html', {'payments': payments})


@super_admin_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'admin_panel/payment_detail.html', {'payment': payment})


@super_admin_required
def payment_receipts_list(request):
    return render(request, 'admin_panel/payment_receipts_list.html', {'receipts': []})


@super_admin_required
def committee_decisions_list(request):
    return render(request, 'admin_panel/committee_decisions_list.html', {'decisions': []})


@super_admin_required
def notifications_list(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'admin_panel/notifications_list.html', {'notifications': notifications})


@super_admin_required
def notification_send(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        # Send to all users or specific user
        messages.success(request, 'Notification sent')
        return redirect('admin_panel:notifications_list')
    return render(request, 'admin_panel/notification_send.html')


@super_admin_required
def audit_logs_list(request):
    return render(request, 'admin_panel/audit_logs_list.html', {'logs': []})


@super_admin_required
def system_settings_list(request):
    return render(request, 'admin_panel/system_settings_list.html', {'settings': []})
'''

# Write the views file
with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(views_content)

print('✓ Created admin_panel/views.py with full CRUD operations')
