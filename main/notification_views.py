# main/notification_views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from main.models import Notification
from main.notification_helper import get_user_notifications, get_unread_count, mark_as_read, mark_all_as_read


def get_time_ago(created_at):
    """Get time ago string for notification"""
    now = timezone.now()
    diff = now - created_at

    if diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


@login_required
def get_notifications_api(request):
    """API endpoint to get user notifications"""
    notifications = get_user_notifications(request.user, 50)
    unread_count = get_unread_count(request.user)

    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'link': notif.link,
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'time_ago': get_time_ago(notif.created_at),
            'is_read': notif.is_read,
        })

    return JsonResponse({
        'notifications': notifications_data,
        'unread_count': unread_count
    })


@login_required
def mark_notification_read(request, notification_id):
    """Mark a single notification as read"""
    if request.method == 'POST':
        success = mark_as_read(notification_id, request.user)
        if success:
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'Notification not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for the user"""
    if request.method == 'POST':
        count = mark_all_as_read(request.user)
        return JsonResponse({'success': True, 'count': count})

    return JsonResponse({'success': False, 'error': 'Invalid request'})