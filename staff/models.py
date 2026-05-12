from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class StaffProfile(models.Model):
    """Staff profile model - ONLY ONE in the system"""
    POSITION_CHOICES = [
        ('loan_officer', 'Loan Officer'),
        ('collections_officer', 'Collections Officer'),
        ('credit_investigator', 'Credit Investigator'),
        ('branch_manager', 'Branch Manager'),
        ('supervisor', 'Supervisor'),
        ('cashier', 'Cashier'),
    ]

    # Basic Information
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='staff_profile'
    )
    staff_id = models.CharField(max_length=20, unique=True)
    position = models.CharField(max_length=100, choices=POSITION_CHOICES, default='loan_officer')
    department = models.CharField(max_length=100, default='Loans')
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='staff_profiles/', null=True, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 2FA Fields
    otp_enabled = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=100, blank=True, null=True)
    otp_backup_codes = models.JSONField(default=list, blank=True)
    otp_enabled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_position_display()}"


class StaffActivityLog(models.Model):
    """Track all staff actions for audit"""
    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=100)  # CREATE, UPDATE, DELETE, REVIEW, APPROVE, etc.
    entity_type = models.CharField(max_length=50)  # application, loan, payment, etc.
    entity_id = models.IntegerField()
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class StaffNotification(models.Model):
    """In-app notifications for staff"""
    NOTIFICATION_TYPES = [
        ('new_application', 'New Application'),
        ('committee_decision', 'Committee Decision'),
        ('manager_decision', 'Manager Decision'),
        ('payment_received', 'Payment Received'),
        ('overdue_alert', 'Overdue Alert'),
        ('restructuring_request', 'Restructuring Request'),
        ('system_alert', 'System Alert'),
    ]

    staff = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class PaymentInstruction(models.Model):
    """Payment instruction slip issued by staff to member"""
    instruction_number = models.CharField(max_length=20, unique=True)
    member_id = models.IntegerField()  # FK to members
    loan_id = models.IntegerField()  # FK to loans
    amount_to_collect = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2)
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    next_due_date = models.DateField()
    is_printed = models.BooleanField(default=False)
    is_collected = models.BooleanField(default=False)
    collected_by_payment_id = models.IntegerField(null=True, blank=True)
    issued_by = models.ForeignKey(StaffProfile, on_delete=models.CASCADE, related_name='issued_instructions')
    issued_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"PI-{self.instruction_number}"


class RestructuringRequest(models.Model):
    """Loan restructuring requests processed by staff"""
    STATUS_CHOICES = [
        ('pending_staff', 'Pending Staff Review'),
        ('with_committee', 'With Committee'),
        ('committee_approved', 'Committee Approved'),
        ('committee_rejected', 'Committee Rejected'),
        ('manager_approved', 'Manager Approved'),
        ('manager_rejected', 'Manager Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    request_number = models.CharField(max_length=20, unique=True)
    member_id = models.IntegerField()
    old_loan_id = models.IntegerField()

    # Old loan details
    old_balance = models.DecimalField(max_digits=12, decimal_places=2)
    old_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    old_penalty = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    days_overdue = models.IntegerField(default=0)

    # New loan calculation
    new_charges = models.DecimalField(max_digits=12, decimal_places=2)
    new_principal = models.DecimalField(max_digits=12, decimal_places=2)
    new_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    new_term_months = models.IntegerField(default=12)
    new_monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)

    # Reason and documents
    reason = models.TextField()
    supporting_documents = models.JSONField(default=list)

    # Approval flow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_staff')

    # Approvals
    staff_approved = models.BooleanField(default=False)
    staff_approved_by = models.ForeignKey(StaffProfile, on_delete=models.SET_NULL, null=True,
                                          related_name='restructuring_staff')
    committee_approved = models.BooleanField(default=False)
    committee_approved_by_id = models.IntegerField(null=True)
    committee_approved_date = models.DateField(null=True)
    manager_approved = models.BooleanField(default=False)
    manager_approved_by_id = models.IntegerField(null=True)
    manager_approved_date = models.DateField(null=True)

    # Result
    new_loan_id = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"RST-{self.request_number}"