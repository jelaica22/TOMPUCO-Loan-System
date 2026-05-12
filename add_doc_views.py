import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add member document management functions
document_functions = '''

@super_admin_required
def member_documents_list(request):
    from main.models import MemberDocument
    from django.db.models import Q
    
    documents = MemberDocument.objects.all().order_by('-uploaded_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    doc_type = request.GET.get('doc_type', '')
    verified_status = request.GET.get('verified_status', '')
    
    # Apply search filter
    if search:
        documents = documents.filter(
            Q(member__first_name__icontains=search) |
            Q(member__last_name__icontains=search) |
            Q(document_number__icontains=search)
        )
    
    # Apply document type filter
    if doc_type and doc_type != 'all':
        documents = documents.filter(document_type=doc_type)
    
    # Apply verification status filter
    if verified_status == 'verified':
        documents = documents.filter(is_verified=True)
    elif verified_status == 'pending':
        documents = documents.filter(is_verified=False)
    
    # Get all members for the dropdown
    all_members = Member.objects.filter(is_active=True)
    
    # Calculate stats
    total_documents = MemberDocument.objects.count()
    verified_count = MemberDocument.objects.filter(is_verified=True).count()
    pending_count = MemberDocument.objects.filter(is_verified=False).count()
    
    return render(request, 'admin_panel/member_documents_list.html', {
        'documents': documents,
        'all_members': all_members,
        'total_documents': total_documents,
        'verified_count': verified_count,
        'pending_count': pending_count,
        'rejected_count': 0,
    })


@super_admin_required
def member_document_create(request):
    from main.models import MemberDocument
    if request.method == 'POST':
        try:
            member_id = request.POST.get('member_id')
            document_type = request.POST.get('document_type')
            document_number = request.POST.get('document_number', '')
            document_file = request.FILES.get('document_file')
            
            member = get_object_or_404(Member, id=member_id)
            
            doc = MemberDocument.objects.create(
                member=member,
                document_type=document_type,
                document_number=document_number,
                file=document_file,
                is_verified=False
            )
            messages.success(request, f'Document uploaded successfully for {member.first_name} {member.last_name}')
        except Exception as e:
            messages.error(request, f'Error uploading document: {str(e)}')
        return redirect('admin_panel:member_documents_list')
    
    return redirect('admin_panel:member_documents_list')


@super_admin_required
def member_document_detail(request, doc_id):
    from main.models import MemberDocument
    from django.http import JsonResponse
    doc = get_object_or_404(MemberDocument, id=doc_id)
    return JsonResponse({
        'id': doc.id,
        'member_name': f"{doc.member.first_name} {doc.member.last_name}",
        'document_type': doc.document_type,
        'document_type_display': dict(MemberDocument.DOCUMENT_TYPES).get(doc.document_type, doc.document_type),
        'document_number': doc.document_number,
        'uploaded_at': doc.uploaded_at.strftime('%Y-%m-%d %H:%M'),
        'is_verified': doc.is_verified,
        'file_url': doc.file.url if doc.file else None,
    })


@super_admin_required
def member_document_verify(request, doc_id):
    from main.models import MemberDocument
    from django.http import JsonResponse
    doc = get_object_or_404(MemberDocument, id=doc_id)
    doc.is_verified = True
    doc.verified_by = request.user
    doc.verified_at = timezone.now()
    doc.save()
    return JsonResponse({'success': True, 'message': 'Document verified'})


@super_admin_required
def member_document_delete(request, doc_id):
    from main.models import MemberDocument
    from django.http import JsonResponse
    doc = get_object_or_404(MemberDocument, id=doc_id)
    if request.method == 'POST':
        doc.delete()
        return JsonResponse({'success': True, 'message': 'Document deleted'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})
'''

# Add the functions to the views file
content = content + document_functions

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added member document management functions')
