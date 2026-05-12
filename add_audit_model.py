import re

with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if AuditLog model exists
if 'class AuditLog' not in content:
    audit_log_model = '''

# Table 13: Audit Logs
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
    ]
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.entity_type} - {self.created_at}"
'''
    content = content + audit_log_model
    with open('main/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added AuditLog model')
