import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add loan attachment management functions
attachment_functions = '''

@super_admin_required
def loan_attachments_list(request):
    from main.models import LoanAttachment, LoanApplication, MemberDocument
    from django.db.models import Q
    
    attachments = LoanAttachment.objects.all().order_by('-attached_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    reused_status = request.GET.get('reused_status', '')
    application_id = request.GET.get('application_id', '')
    
    # Apply search filter
    if search:
        attachments = attachments.filter(
            Q(loan_application__application_id__icontains=search) |
            Q(loan_application__member__first_name__icontains=search) |
            Q(loan_application__member__last_name__icontains=search)
        )
    
    # Apply reused status filter
    if reused_status == 'reused':
        attachments = attachments.filter(is_reused=True)
    elif reused_status == 'new':
        attachments = attachments.filter(is_reused=False)
    
    # Apply application filter
    if application_id and application_id != 'all':
        attachments = attachments.filter(loan_application_id=application_id)
    
    all_applications = LoanApplication.objects.all().order_by('-created_at')
    all_documents = MemberDocument.objects.all()
    
    # Calculate stats
    total_attachments = LoanAttachment.objects.count()
    reused_count = LoanAttachment.objects.filter(is_reused=True).count()
    new_count = LoanAttachment.objects.filter(is_reused=False).count()
    applications_count = LoanApplication.objects.count()
    
    return render(request, 'admin_panel/loan_attachments_list.html', {
        'attachments': attachments,
        'all_applications': all_applications,
        'all_documents': all_documents,
        'total_attachments': total_attachments,
        'reused_count': reused_count,
        'new_count': new_count,
        'applications_count': applications_count,
    })


@super_admin_required
def loan_attachment_create(request):
    from main.models import LoanAttachment, LoanApplication, MemberDocument
    if request.method == 'POST':
        try:
            application_id = request.POST.get('application_id')
            document_id = request.POST.get('document_id')
            is_reused = request.POST.get('is_reused') == 'on'
            
            loan_app = get_object_or_404(LoanApplication, id=application_id)
            document = get_object_or_404(MemberDocument, id=document_id)
            
            attachment = LoanAttachment.objects.create(
                loan_application=loan_app,
                document=document,
                is_reused=is_reused
            )
            messages.success(request, f'Attachment added to application {loan_app.application_id}')
        except Exception as e:
            messages.error(request, f'Error adding attachment: {str(e)}')
        return redirect('admin_panel:loan_attachments_list')
    
    return redirect('admin_panel:loan_attachments_list')


@super_admin_required
def loan_attachment_detail(request, att_id):
    from main.models import LoanAttachment
    from django.http import JsonResponse
    att = get_object_or_404(LoanAttachment, id=att_id)
    return JsonResponse({
        'id': att.id,
        'application_id': att.loan_application.application_id,
        'member_name': f"{att.loan_application.member.first_name} {att.loan_application.member.last_name}",
        'document_type': att.document.get_document_type_display(),
        'document_number': att.document.document_number,
        'is_reused': att.is_reused,
        'attached_at': att.attached_at.strftime('%Y-%m-%d %H:%M'),
        'file_url': att.document.file.url if att.document.file else None,
    })


@super_admin_required
def loan_attachment_delete(request, att_id):
    from main.models import LoanAttachment
    from django.http import JsonResponse
    att = get_object_or_404(LoanAttachment, id=att_id)
    if request.method == 'POST':
        att.delete()
        return JsonResponse({'success': True, 'message': 'Attachment deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})
'''

# Add the functions to the views file
content = content + attachment_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added loan attachment management functions')
