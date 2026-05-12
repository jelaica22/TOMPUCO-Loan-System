import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add audit logging to user_create, user_edit, user_delete
audit_logging_code = '''

# Helper function to get client IP
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Add audit logging to user_create
def _log_audit(user, action, entity_type, entity_id, old_values=None, new_values=None, request=None):
    from main.models import AuditLog
    try:
        audit = AuditLog(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            old_values=old_values,
            new_values=new_values,
        )
        if request:
            audit.ip_address = get_client_ip(request)
            audit.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        audit.save()
    except Exception as e:
        print(f"Audit log error: {e}")
'''

# Insert audit logging code after imports
if 'def get_client_ip' not in content:
    content = content.replace('from main.models import (', 'from main.models import (\n    AuditLog,')
    content = content + '\n' + audit_logging_code

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Added audit logging helper functions')
