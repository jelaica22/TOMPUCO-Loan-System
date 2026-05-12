with open('admin_panel/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('member-documents/create/'" not in content:
    new_urls = """
    path('member-documents/create/', views.member_document_create, name='member_document_create'),
    path('member-documents/<int:doc_id>/', views.member_document_detail, name='member_document_detail'),
    path('member-documents/<int:doc_id>/verify/', views.member_document_verify, name='member_document_verify'),
    path('member-documents/<int:doc_id>/delete/', views.member_document_delete, name='member_document_delete'),
"""
    content = content.replace(
        "path('member-documents/', views.member_documents_list, name='member_documents_list'),",
        "path('member-documents/', views.member_documents_list, name='member_documents_list'),\n    " + new_urls
    )
    with open('admin_panel/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added document management URLs')
