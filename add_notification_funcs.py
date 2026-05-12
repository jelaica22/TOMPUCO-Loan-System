with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

notification_functions = '''

@login_required
@staff_required
def get_notifications(request):
    """Get staff notifications"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:20]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    data = {
        'notifications': [
            {'id': n.id, 'title': n.title, 'message': n.message, 
             'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'), 'is_read': n.is_read}
            for n in notifications
        ],
        'unread_count': unread_count
    }
    return JsonResponse(data)


@login_required
@staff_required
def mark_notification_read(request, notif_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notif_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'success': True})
'''

if 'def get_notifications' not in content:
    content = content + notification_functions
    with open('staff/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added notification functions to staff')
