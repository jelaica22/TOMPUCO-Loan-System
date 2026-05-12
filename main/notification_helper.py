# main/notification_helper.py
from django.contrib.auth.models import User
from main.models import Notification

def create_notification(recipient, notification_type, title, message, link=None):
    """Create a notification for a specific user"""
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
    return notification


def notify_staff(notification_type, title, message, link=None):
    """Send notification to all staff members"""
    staff_users = User.objects.filter(is_staff=True)
    notifications = []
    for user in staff_users:
        notifications.append(
            Notification(
                recipient=user,
                notification_type=notification_type,
                title=title,
                message=message,
                link=link
            )
        )
    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_user_by_id(user_id, notification_type, title, message, link=None):
    """Send notification to a specific user by ID"""
    try:
        user = User.objects.get(id=user_id)
        return create_notification(user, notification_type, title, message, link)
    except User.DoesNotExist:
        return None


def get_user_notifications(user, limit=50):
    """Get notifications for a user"""
    return Notification.objects.filter(recipient=user).order_by('-created_at')[:limit]


def get_unread_count(user):
    """Get unread notification count for a user"""
    return Notification.objects.filter(recipient=user, is_read=False).count()


def mark_as_read(notification_id, user):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id, recipient=user)
        notification.is_read = True
        notification.save()
        return True
    except Notification.DoesNotExist:
        return False


def mark_all_as_read(user):
    """Mark all notifications as read for a user"""
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)