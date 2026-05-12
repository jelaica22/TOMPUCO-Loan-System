import os
import sys

# Read the current models.py
with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if models already exist
if 'class MemberDocument' not in content:
    new_models = '''

# Table 5: Member Documents
class MemberDocument(models.Model):
    DOCUMENT_TYPES = [
        ('valid_id', 'Valid ID'),
        ('proof_income', 'Proof of Income'),
        ('collateral', 'Collateral Document'),
        ('others', 'Others'),
    ]
    member = models.ForeignKey('Member', on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='member_documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - {self.get_document_type_display()}"


# Table 6: Loan Attachments
class LoanAttachment(models.Model):
    loan_application = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name='attachments')
    document = models.ForeignKey(MemberDocument, on_delete=models.CASCADE)
    is_reused = models.BooleanField(default=False)
    attached_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for {self.loan_application.application_id}"


# Table 10: Payment Receipts
class PaymentReceipt(models.Model):
    receipt_number = models.CharField(max_length=50, unique=True)
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name='receipts')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=[('cash', 'Cash'), ('bank', 'Bank Transfer'), ('check', 'Check')])
    receipt_pdf = models.FileField(upload_to='receipts/%Y/%m/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from django.utils import timezone
            year = timezone.now().year
            last_receipt = PaymentReceipt.objects.filter(receipt_number__startswith=f'RCP-{year}').order_by('-id').first()
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                self.receipt_number = f'RCP-{year}-{str(last_num + 1).zfill(6)}'
            else:
                self.receipt_number = f'RCP-{year}-000001'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.receipt_number


# Table 11: Committee Decisions
class CommitteeDecision(models.Model):
    loan_application = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name='committee_decisions')
    committee_member = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True})
    approved_line_amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_approved = models.DateField(auto_now_add=True)
    reduction_reason = models.TextField(blank=True)
    decision = models.CharField(max_length=20, choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('revision', 'Needs Revision')])
    comments = models.TextField(blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Decision for {self.loan_application.application_id}"


# Table 13: Audit Logs
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    user = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.entity_type}"


# Table 14: System Settings
class SystemSetting(models.Model):
    SETTING_TYPES = [
        ('general', 'General'),
        ('loan', 'Loan Settings'),
        ('payment', 'Payment Settings'),
        ('notification', 'Notification Settings'),
    ]
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    setting_type = models.CharField(max_length=50, choices=SETTING_TYPES, default='general')
    description = models.TextField(blank=True)
    updated_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.setting_key} = {self.setting_value}"
'''

    # Append the new models to the file
    content = content.rstrip() + new_models
    with open('main/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added missing models to main/models.py')
else:
    print('✓ Models already exist')
