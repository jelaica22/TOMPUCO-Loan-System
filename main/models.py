# main/models.py - COMPLETE CORRECTED VERSION

from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta
import random


def generate_membership_number():
    import random
    while True:
        number = f"M-{random.randint(10000, 99999)}"
        if not Member.objects.filter(membership_number=number).exists():
            return number


def generate_employee_id():
    """Generate employee ID for cooperative employees"""
    year = date.today().year
    last_employee = Member.objects.filter(employee_id__startswith=f'EMP-{year}').count()
    new_num = last_employee + 1
    return f"EMP-{year}-{new_num:04d}"


class Member(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    PAYMENT_MODE_CHOICES = [('monthly', 'Monthly'), ('weekly', 'Weekly'), ('others', 'Others')]

    CIVIL_STATUS = [
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('separated', 'Legally Separated'),
    ]

    ACCOUNT_STATUS = [
        ('pending', '⏳ Pending Verification'),
        ('active', '✅ Active'),
        ('suspended', '⚠️ Suspended'),
        ('inactive', '❌ Inactive'),
        ('rejected', '🚫 Rejected'),
        ('blocked', '🔒 Blocked'),
    ]

    EMPLOYMENT_STATUS = [
        ('non_employee', 'Regular Member'),
        ('employee', 'Employee Member'),
    ]

    VERIFICATION_STATUS = [
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('needs_review', 'Needs Additional Review'),
    ]

    MEMBER_TIER = [
        ('basic', 'Basic (Unverified)'),
        ('standard', 'Standard (Verified)'),
        ('premium', 'Premium (Fully Verified)'),
        ('vip', 'VIP Member'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    membership_number = models.CharField(max_length=50, unique=True, default=generate_membership_number)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    civil_status = models.CharField(max_length=20, choices=CIVIL_STATUS, default='single')
    birthdate = models.DateField(null=True, blank=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    nationality = models.CharField(max_length=50, default='Filipino')
    contact_number = models.CharField(max_length=20)
    residence_address = models.TextField()
    spouse_name = models.CharField(max_length=200, blank=True, null=True)
    num_dependents = models.IntegerField(default=0)

    # Farm Information
    farm_location = models.CharField(max_length=500, blank=True, null=True)
    farm_owned_hectares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    farm_leased_hectares = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    area_planted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_plant = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ratoon_crops = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    adjacent_farm = models.CharField(max_length=500, blank=True, null=True)

    # Employment
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='non_employee')
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    date_hired = models.DateField(null=True, blank=True)

    # Income
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_income_sources = models.TextField(blank=True, null=True)
    other_loans = models.TextField(blank=True, null=True)

    # Employer Information
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    employer_address = models.CharField(max_length=500, blank=True, null=True)
    years_with_employer = models.IntegerField(default=0)
    supervisor_name = models.CharField(max_length=200, blank=True, null=True)
    previous_employer = models.CharField(max_length=200, blank=True, null=True)

    # Bank
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    bank_account_type = models.CharField(max_length=20, blank=True, null=True)

    # Address History
    years_in_address = models.IntegerField(null=True, blank=True)
    years_in_community = models.IntegerField(null=True, blank=True)

    # Self Employment
    self_employed_firm = models.CharField(max_length=200, blank=True, null=True)
    self_employed_address = models.TextField(blank=True, null=True)
    self_employed_business_kind = models.CharField(max_length=200, blank=True, null=True)
    years_in_business = models.IntegerField(null=True, blank=True)
    trade_reference = models.CharField(max_length=200, blank=True, null=True)

    # Co-maker Relationship
    years_known_applicant = models.IntegerField(null=True, blank=True)
    is_related_to_applicant = models.BooleanField(default=False)
    relationship_type = models.CharField(max_length=100, blank=True, null=True)
    has_been_borrower = models.BooleanField(default=False)
    previous_lender = models.CharField(max_length=200, blank=True, null=True)
    has_been_comaker = models.BooleanField(default=False)
    previous_borrower_name = models.CharField(max_length=200, blank=True, null=True)

    # Loan Limits
    salary_loan_eligible = models.BooleanField(default=False)
    max_regular_loan = models.DecimalField(max_digits=12, decimal_places=2, default=10000)
    max_salary_loan = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_active_loans = models.IntegerField(default=0)

    # Account Status
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS, default='pending')
    status_updated_at = models.DateTimeField(null=True, blank=True)
    status_updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='status_updates')
    status_reason = models.TextField(blank=True, null=True)

    # Verification
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')
    verification_date = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='verified_members')
    verification_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)

    member_tier = models.CharField(max_length=20, choices=MEMBER_TIER, default='basic')
    valid_id_verified = models.BooleanField(default=False)

    # Account Flags
    is_active = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_restricted = models.BooleanField(default=False)
    restriction_reason = models.TextField(blank=True, null=True)
    restricted_until = models.DateField(null=True, blank=True)

    # Documents
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    uploaded_id = models.FileField(upload_to='valid_ids/', blank=True, null=True)
    signature = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.birthdate:
            today = date.today()
            self.age = today.year - self.birthdate.year - (
                    (today.month, today.day) < (self.birthdate.month, self.birthdate.day))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.membership_number})"


# Loan related models
class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('paid', 'Paid'),
        ('defaulted', 'Defaulted'),
        ('restructured', 'Restructured'),
        ('overdue', 'Overdue'),
    ]

    loan_number = models.CharField(max_length=50, unique=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    total_payable = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    disbursement_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Loan {self.loan_number} - {self.member}"


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('pesada', 'Pesada'),
        ('quedan', 'Quedan'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('voided', 'Voided'),
    ]

    payment_number = models.CharField(max_length=50, unique=True, blank=True)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True)

    principal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_balance_after = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    is_posted = models.BooleanField(default=True)
    posted_at = models.DateTimeField(auto_now_add=True)

    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='issued_payments')
    posted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='posted_payments')

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.payment_number:
            year = date.today().year
            last_payment = Payment.objects.filter(payment_number__startswith=f'PAY-{year}').order_by(
                '-payment_number').first()
            if last_payment:
                try:
                    last_num = int(last_payment.payment_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.payment_number = f'PAY-{year}-{new_num:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_number


class LoanProduct(models.Model):
    LOAN_TYPE_CHOICES = [
        ('NCL', 'NCL - Non-Collateralized Loan'),
        ('APCP', 'APCP - Agricultural Production Credit Program'),
        ('SALARY', 'SALARY - Salary Loan'),
        ('COLLATERAL', 'COLLATERAL - Secured Loan'),
        ('PROVIDENTIAL', 'PROVIDENTIAL - Providential Loan'),
        ('B2B', 'B2B - Back to Back Loan'),
        ('TRADE', 'TRADE - Trade Loan')
    ]

    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=200)
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPE_CHOICES)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_months = models.IntegerField(default=12)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    requires_comaker = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    penalty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
        ('committee', 'With Committee'),
    ]

    approved_line = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Approved Line Amount"
    )
    committee_approved_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Committee Approval Date"
    )
    committee_reduction_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name="Reason for Reduction"
    )

    application_id = models.CharField(max_length=50, unique=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='applications')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateField(auto_now_add=True)
    reviewed_date = models.DateField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Application {self.application_id} - {self.member}"


class CommitteeVote(models.Model):
    VOTE_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('request_revision', 'Request Revision'),
    ]

    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='committee_votes')
    committee_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='committee_votes')
    vote = models.CharField(max_length=20, choices=VOTE_CHOICES)
    approved_line = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    reduction_reason = models.TextField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['application', 'committee_member']

    def __str__(self):
        return f"{self.committee_member.username} - {self.application.application_id} - {self.vote}"


class PaymentSchedule(models.Model):
    """Payment Schedule Model"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ]

    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='schedules')
    schedule_number = models.IntegerField()
    due_date = models.DateField()
    principal_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"Schedule {self.schedule_number} - Loan {self.loan.loan_number}"


class MemberDocument(models.Model):
    """Member Documents Model"""
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
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member} - {self.get_document_type_display()}"


class PaymentReceipt(models.Model):
    """Payment Receipt Model"""
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    payment = models.OneToOneField('Payment', on_delete=models.CASCADE, related_name='receipt')
    member = models.ForeignKey('Member', on_delete=models.CASCADE)

    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20)
    payment_date = models.DateField()
    payment_time = models.TimeField(auto_now_add=True)

    principal_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    penalty_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    next_due_date = models.DateField(null=True, blank=True)
    estimated_next_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    receipt_pdf = models.FileField(upload_to='receipts/%Y/%m/%d/', blank=True, null=True)
    issued_by = models.CharField(max_length=200, blank=True)
    posted_by = models.CharField(max_length=200, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            from datetime import date
            year = date.today().year
            last_receipt = PaymentReceipt.objects.filter(
                receipt_number__startswith=f'RCP-{year}'
            ).order_by('-receipt_number').first()
            if last_receipt:
                try:
                    last_num = int(last_receipt.receipt_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = 1
            else:
                new_num = 1
            self.receipt_number = f'RCP-{year}-{new_num:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class PaymentReminder(models.Model):
    """Payment Reminder Model"""
    REMINDER_TYPES = [
        ('7_days', '7 Days Before Due'),
        ('3_days', '3 Days Before Due'),
        ('1_day', '1 Day Before Due'),
        ('due_date', 'Due Date'),
        ('overdue_7', '7 Days Overdue'),
        ('overdue_15', '15 Days Overdue'),
        ('overdue_30', '30 Days Overdue'),
    ]

    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Reminder for {self.loan.loan_number} - {self.get_reminder_type_display()}"


class CommitteeDecision(models.Model):
    """Committee Decision Model"""
    loan_application = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name='committee_decisions')
    committee_member = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_staff': True})
    approved_line_amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_approved = models.DateField(auto_now_add=True)
    reduction_reason = models.TextField(blank=True)
    decision = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision', 'Needs Revision')
    ])
    comments = models.TextField(blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Decision for {self.loan_application.application_id}"


class LoanAttachment(models.Model):
    """Loan Attachments Model"""
    loan_application = models.ForeignKey('LoanApplication', on_delete=models.CASCADE, related_name='attachments')
    document = models.ForeignKey('MemberDocument', on_delete=models.CASCADE)
    is_reused = models.BooleanField(default=False)
    attached_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.loan_application.application_id}"


class Notification(models.Model):
    """Notification Model"""
    NOTIFICATION_TYPES = [
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('application', 'Application'),
        ('payment', 'Payment'),
        ('loan', 'Loan'),
        ('system', 'System'),
        ('alert', 'Alert'),
        ('approval', 'Approval'),
        ('committee', 'Committee'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


class SystemSetting(models.Model):
    """System Settings Model"""
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
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.setting_key} = {self.setting_value}"


class AuditLog(models.Model):
    """Audit Log Model"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
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

    civil_status = models.CharField(max_length=20, blank=True, null=True)
    employment_status = models.CharField(max_length=20, default='member')
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    date_hired = models.DateField(blank=True, null=True)
    salary_loan_eligible = models.BooleanField(default=False)
    max_regular_loan = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    max_salary_loan = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    max_active_loans = models.IntegerField(default=0)
    verification_status = models.CharField(max_length=20, default='pending')
    account_status = models.CharField(max_length=20, default='pending')
    member_tier = models.CharField(max_length=20, default='basic')