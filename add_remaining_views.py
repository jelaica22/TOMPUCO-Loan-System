import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add missing view functions for Tables 11-14
new_views = '''

# ==================== TABLE 11: COMMITTEE DECISIONS ====================
@super_admin_required
def committee_decisions_list(request):
    from main.models import CommitteeDecision
    from django.db.models import Q
    from datetime import datetime
    
    decisions = CommitteeDecision.objects.all().order_by('-voted_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    decision_filter = request.GET.get('decision', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search filter
    if search:
        decisions = decisions.filter(
            Q(loan_application__application_id__icontains=search) |
            Q(loan_application__member__first_name__icontains=search) |
            Q(loan_application__member__last_name__icontains=search)
        )
    
    # Apply decision filter
    if decision_filter and decision_filter != 'all':
        decisions = decisions.filter(decision=decision_filter)
    
    # Apply date filters
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            decisions = decisions.filter(voted_at__date__gte=date_from_parsed)
        except:
            pass
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            decisions = decisions.filter(voted_at__date__lte=date_to_parsed)
        except:
            pass
    
    # Calculate stats
    total_decisions = CommitteeDecision.objects.count()
    approved_count = CommitteeDecision.objects.filter(decision='approved').count()
    rejected_count = CommitteeDecision.objects.filter(decision='rejected').count()
    revision_count = CommitteeDecision.objects.filter(decision='revision').count()
    
    return render(request, 'admin_panel/committee_decisions_list.html', {
        'decisions': decisions,
        'total_decisions': total_decisions,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'revision_count': revision_count,
    })


@super_admin_required
def committee_decision_detail(request, decision_id):
    from django.http import JsonResponse
    from main.models import CommitteeDecision
    decision = get_object_or_404(CommitteeDecision, id=decision_id)
    return JsonResponse({
        'id': decision.id,
        'application_id': decision.loan_application.application_id,
        'member_name': f"{decision.loan_application.member.first_name} {decision.loan_application.member.last_name}",
        'requested_amount': str(decision.loan_application.requested_amount),
        'approved_line_amount': str(decision.approved_line_amount),
        'decision': decision.decision,
        'decision_display': dict(decision.DECISION_CHOICES).get(decision.decision, decision.decision),
        'reduction_reason': decision.reduction_reason,
        'comments': decision.comments,
        'committee_member': decision.committee_member.get_full_name() if decision.committee_member else 'System',
        'date': decision.voted_at.strftime('%Y-%m-%d %H:%M'),
    })


@super_admin_required
def committee_decision_delete(request, decision_id):
    from django.http import JsonResponse
    from main.models import CommitteeDecision
    decision = get_object_or_404(CommitteeDecision, id=decision_id)
    if request.method == 'POST':
        decision.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# ==================== TABLE 12: NOTIFICATIONS ====================
@super_admin_required
def notifications_list(request):
    from main.models import Notification
    from django.db.models import Q
    
    notifications = Notification.objects.all().order_by('-created_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '')
    
    if search:
        notifications = notifications.filter(
            Q(title__icontains=search) |
            Q(message__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    if status_filter == 'read':
        notifications = notifications.filter(is_read=True)
    elif status_filter == 'unread':
        notifications = notifications.filter(is_read=False)
    
    total_notifications = Notification.objects.count()
    read_count = Notification.objects.filter(is_read=True).count()
    unread_count = Notification.objects.filter(is_read=False).count()
    
    return render(request, 'admin_panel/notifications_list.html', {
        'notifications': notifications,
        'total_notifications': total_notifications,
        'read_count': read_count,
        'unread_count': unread_count,
    })


@super_admin_required
def notification_mark_read(request, notif_id):
    from django.http import JsonResponse
    from main.models import Notification
    notification = get_object_or_404(Notification, id=notif_id)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})


@super_admin_required
def notification_delete(request, notif_id):
    from django.http import JsonResponse
    from main.models import Notification
    notification = get_object_or_404(Notification, id=notif_id)
    if request.method == 'POST':
        notification.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


# ==================== TABLE 13: AUDIT LOGS ====================
@super_admin_required
def audit_logs_list(request):
    from main.models import AuditLog
    from django.db.models import Q
    
    logs = AuditLog.objects.all().order_by('-created_at')
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    action_filter = request.GET.get('action', '')
    
    if search:
        logs = logs.filter(
            Q(user__username__icontains=search) |
            Q(entity_type__icontains=search)
        )
    
    if action_filter and action_filter != 'all':
        logs = logs.filter(action=action_filter)
    
    total_logs = AuditLog.objects.count()
    create_count = AuditLog.objects.filter(action='create').count()
    update_count = AuditLog.objects.filter(action='update').count()
    delete_count = AuditLog.objects.filter(action='delete').count()
    
    return render(request, 'admin_panel/audit_logs_list.html', {
        'logs': logs,
        'total_logs': total_logs,
        'create_count': create_count,
        'update_count': update_count,
        'delete_count': delete_count,
    })


@super_admin_required
def audit_log_detail(request, log_id):
    from django.http import JsonResponse
    from main.models import AuditLog
    log = get_object_or_404(AuditLog, id=log_id)
    return JsonResponse({
        'id': log.id,
        'user': log.user.username if log.user else 'System',
        'action': log.action,
        'entity_type': log.entity_type,
        'entity_id': log.entity_id,
        'old_values': log.old_values,
        'new_values': log.new_values,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
    })


# ==================== TABLE 14: SYSTEM SETTINGS ====================
@super_admin_required
def system_settings_list(request):
    from main.models import SystemSetting
    
    settings = SystemSetting.objects.all().order_by('setting_key')
    
    return render(request, 'admin_panel/system_settings_list.html', {
        'settings': settings,
    })


@super_admin_required
def system_setting_update(request, setting_id):
    from django.http import JsonResponse
    from main.models import SystemSetting
    from decimal import Decimal
    
    setting = get_object_or_404(SystemSetting, id=setting_id)
    if request.method == 'POST':
        setting.setting_value = request.POST.get('value', setting.setting_value)
        setting.updated_by = request.user
        setting.save()
        return JsonResponse({'success': True, 'value': setting.setting_value})
    return JsonResponse({'success': False})
'''

# Add the functions to the views file
content = content + new_views

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added view functions for Tables 11-14')
