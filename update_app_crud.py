import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Complete replacement for loan applications functions
new_functions = '''

@super_admin_required
def loan_applications_list(request):
    from django.db.models import Q
    from datetime import datetime
    
    # Start with all applications
    applications = LoanApplication.objects.all().order_by('-created_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', 'all')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search filter
    if search:
        applications = applications.filter(
            Q(application_id__icontains=search) |
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search) |
            Q(member__membership_number__icontains=search)
        )
    
    # Apply status filter
    if status and status != 'all':
        applications = applications.filter(status=status)
    
    # Apply date filters
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            applications = applications.filter(created_at__date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            applications = applications.filter(created_at__date__lte=date_to_parsed)
        except:
            pass
    
    # Count stats
    total_applications = LoanApplication.objects.count()
    pending_count = LoanApplication.objects.filter(status='pending_staff_review').count()
    committee_count = LoanApplication.objects.filter(status='with_committee').count()
    approved_count = LoanApplication.objects.filter(status__in=['line_approved', 'manager_approved']).count()
    rejected_count = LoanApplication.objects.filter(status='rejected').count()
    
    return render(request, 'admin_panel/loan_applications_list.html', {
        'applications': applications,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'committee_count': committee_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@super_admin_required
def loan_application_detail(request, app_id):
    """Get application details as JSON"""
    from django.http import JsonResponse
    app = get_object_or_404(LoanApplication, id=app_id)
    return JsonResponse({
        "id": app.id,
        "application_id": app.application_id,
        "member_name": f"{app.member.first_name} {app.member.last_name}",
        "member_id": app.member.membership_number,
        "requested_amount": str(app.requested_amount),
        "approved_line": str(app.approved_line) if app.approved_line else "0",
        "net_proceeds": str(app.net_proceeds) if app.net_proceeds else "0",
        "service_charge": str(app.service_charge) if app.service_charge else "0",
        "cbu_retention": str(app.cbu_retention) if app.cbu_retention else "0",
        "insurance_charge": str(app.insurance_charge) if app.insurance_charge else "0",
        "status": app.status,
        "loan_product": app.loan_product.name if app.loan_product else "-",
        "purpose": app.purpose or "-",
        "collateral": app.collateral_offered or "-",
        "co_maker": f"{app.co_maker.first_name} {app.co_maker.last_name}" if app.co_maker else "None",
        "date_applied": app.created_at.strftime("%Y-%m-%d %H:%M") if app.created_at else "-",
    })


@super_admin_required
def loan_application_create(request):
    """Create new loan application"""
    from decimal import Decimal
    if request.method == 'POST':
        try:
            member_id = request.POST.get('member_id')
            product_id = request.POST.get('product_id')
            amount = Decimal(request.POST.get('amount', 0))
            purpose = request.POST.get('purpose', '')
            collateral = request.POST.get('collateral', '')
            
            member = get_object_or_404(Member, id=member_id)
            product = get_object_or_404(LoanProduct, id=product_id)
            
            # Generate application ID
            import random
            app_id = f"{product.name}-{datetime.now().year}-{random.randint(1000, 9999)}"
            
            application = LoanApplication.objects.create(
                application_id=app_id,
                member=member,
                loan_product=product,
                requested_amount=amount,
                purpose=purpose,
                collateral_offered=collateral,
                status='pending_staff_review',
                applicant_user=member.user
            )
            messages.success(request, f'Application {app_id} created successfully')
            return redirect('admin_panel:loan_applications_list')
        except Exception as e:
            messages.error(request, f'Error creating application: {str(e)}')
            return redirect('admin_panel:loan_applications_list')
    
    # GET request - show create form
    members = Member.objects.filter(is_active=True)
    products = LoanProduct.objects.filter(is_active=True)
    return render(request, 'admin_panel/loan_application_form.html', {
        'members': members,
        'products': products,
        'action': 'Create'
    })


@super_admin_required
def loan_application_edit(request, app_id):
    """Edit loan application"""
    from decimal import Decimal
    app = get_object_or_404(LoanApplication, id=app_id)
    
    if request.method == 'POST':
        try:
            app.requested_amount = Decimal(request.POST.get('amount', 0))
            app.purpose = request.POST.get('purpose', '')
            app.collateral_offered = request.POST.get('collateral', '')
            app.status = request.POST.get('status', app.status)
            app.save()
            messages.success(request, f'Application {app.application_id} updated successfully')
            return redirect('admin_panel:loan_applications_list')
        except Exception as e:
            messages.error(request, f'Error updating application: {str(e)}')
            return redirect('admin_panel:loan_applications_list')
    
    members = Member.objects.filter(is_active=True)
    products = LoanProduct.objects.filter(is_active=True)
    return render(request, 'admin_panel/loan_application_form.html', {
        'app': app,
        'members': members,
        'products': products,
        'action': 'Edit'
    })


@super_admin_required
def loan_application_delete(request, app_id):
    """Delete application"""
    from django.http import JsonResponse
    app = get_object_or_404(LoanApplication, id=app_id)
    if request.method == 'POST':
        app_id_display = app.application_id
        app.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": f"Application {app_id_display} deleted"})
        messages.success(request, f'Application {app_id_display} deleted')
        return redirect('admin_panel:loan_applications_list')
    return render(request, 'admin_panel/loan_application_confirm_delete.html', {'app': app})
'''

# Remove old functions and add new ones
import re
pattern1 = r'def loan_applications_list\(request\).*?(?=\n@super_admin_required|\n\Z)'
pattern2 = r'def loan_application_detail\(request, app_id\).*?(?=\n@super_admin_required|\n\Z)'
pattern3 = r'def loan_application_delete\(request, app_id\).*?(?=\n@super_admin_required|\n\Z)'

content = re.sub(pattern1, '', content, flags=re.DOTALL)
content = re.sub(pattern2, '', content, flags=re.DOTALL)
content = re.sub(pattern3, '', content, flags=re.DOTALL)

# Add the new functions before the last function
content = content.rstrip() + new_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated loan_applications view with full CRUD and proper filtering')
