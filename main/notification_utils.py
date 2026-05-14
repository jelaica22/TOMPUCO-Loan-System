# main/notification_utils.py

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification


def send_realtime_notification(user, title, message, link='#', notification_type='system'):
    """
    Send a real-time notification to a specific user
    """
    # Create the notification in database
    notification = Notification.objects.create(
        recipient=user,
        title=title,
        message=message,
        link=link,
        notification_type=notification_type,
        is_read=False
    )

    # Get unread count for this user
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()

    # Prepare notification data
    from django.utils.timesince import timesince
    notification_data = {
        'id': notification.id,
        'title': notification.title,
        'message': notification.message,
        'link': notification.link,
        'created_at': notification.created_at.isoformat(),
        'is_read': notification.is_read,
        'time_ago': 'Just now'
    }

    # Send via WebSocket
    channel_layer = get_channel_layer()
    group_name = f'notifications_{user.id}'

    try:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'new_notification',
                'notification': notification_data,
                'unread_count': unread_count
            }
        )
    except Exception as e:
        print(f"Error sending realtime notification: {e}")

    return notification


def send_realtime_notification_to_group(users, title, message, link='#', notification_type='system'):
    """
    Send real-time notification to multiple users
    """
    notifications = []
    for user in users:
        notif = send_realtime_notification(user, title, message, link, notification_type)
        notifications.append(notif)
    return notifications