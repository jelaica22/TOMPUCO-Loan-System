# Create audit_logger.py in the main app
import json
from django.utils import timezone
from django.contrib.auth.models import User
from .models import AuditLog

def log_audit_action(user, action, entity_type, entity_id=None, old_values=None, new_values=None, request=None):
    """Log an audit action to the database"""
    try:
        log = AuditLog(
            user=user if user and user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else '',
            old_values=old_values,
            new_values=new_values,
        )
        if request:
            log.ip_address = get_client_ip(request)
            log.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        log.save()
    except Exception as e:
        print(f"Error logging audit: {e}")

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_create(user, entity_type, entity_id, entity_data, request=None):
    """Log a create action"""
    log_audit_action(user, 'create', entity_type, entity_id, 
                     old_values=None, new_values=entity_data, request=request)

def log_update(user, entity_type, entity_id, old_values, new_values, request=None):
    """Log an update action"""
    log_audit_action(user, 'update', entity_type, entity_id,
                     old_values=old_values, new_values=new_values, request=request)

def log_delete(user, entity_type, entity_id, entity_data, request=None):
    """Log a delete action"""
    log_audit_action(user, 'delete', entity_type, entity_id,
                     old_values=entity_data, new_values=None, request=request)

def log_view(user, entity_type, entity_id, request=None):
    """Log a view action"""
    log_audit_action(user, 'view', entity_type, entity_id, request=request)
