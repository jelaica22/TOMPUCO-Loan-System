from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.conf import settings
from datetime import date, timedelta
import random
import uuid


def generate_membership_number():
    return f"M-{random.randint(10000, 99999)}"


def generate_application_id():
    year = date.today().year
    return f"APCP-{year}-{random.randint(1000, 9999)}"


def generate_loan_number():
    year = date.today().year
    return f"LN-{year}-{random.randint(1000, 9999)}"


# ============================================================
# MEMBER MODEL
# ============================================================
class Member(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female')]
    PAYMENT_MODE_CHOICES = [('monthly', 'Monthly'), ('weekly', 'Weekly'), ('others', 'Others')]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('suspended', 'Suspended')]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    membership_number = models.CharField(max_length=50, unique=True, default=generate_membership_number)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
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
    is_employee = models.BooleanField(default=False)
    employer_name = models.CharField(max_length=200, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    monthly_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Income
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_income_sources = models.TextField(blank=True, null=True)
    other_loans = models.TextField(blank=True, null=True)

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

    # Real Estate
    real_estate_1 = models.TextField(blank=True, null=True)
    real_estate_1_owner = models.CharField(max_length=200, blank=True, null=True)
    real_estate_1_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    real_estate_1_mortgage = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    real_estate_2 = models.TextField(blank=True, null=True)
    real_estate_2_owner = models.CharField(max_length=200, blank=True, null=True)
    real_estate_2_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    real_estate_2_mortgage = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    real_estate_3 = models.TextField(blank=True, null=True)
    real_estate_3_owner = models.CharField(max_length=200, blank=True, null=True)
    real_estate_3_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    real_estate_3_mortgage = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Co-maker Relationship
    years_known_applicant = models.IntegerField(null=True, blank=True)
    is_related_to_applicant = models.BooleanField(default=False)
    relationship_type = models.CharField(max_length=100, blank=True, null=True)
    has_been_borrower = models.BooleanField(default=False)
    previous_lender = models.CharField(max_length=200, blank=True, null=True)
    has_been_comaker = models.BooleanField(default=False)
    previous_borrower_name = models.CharField(max_length=200, blank=True, null=True)

    # Documents
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    uploaded_id = models.FileField(upload_to='valid_ids/', blank=True, null=True)
    signature = models.TextField(blank=True, null=True)

    # Collateral Documents
    collateral_document = models.FileField(upload_to='collateral_docs/%Y/%m/%d/', null=True, blank=True)
    collateral_document_type = models.CharField(max_length=100, blank=True, null=True)
    collateral_document_number = models.CharField(max_length=100, blank=True, null=True)
    collateral_issued_by = models.CharField(max_length=200, blank=True, null=True)
    collateral_issue_date = models.DateField(null=True, blank=True)
    collateral_expiry_date = models.DateField(null=True, blank=True)
    collateral_property_description = models.TextField(blank=True, null=True)
    collateral_area = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    collateral_uploaded_at = models.DateTimeField(auto_now_add=True, null=True)
    collateral_is_verified = models.BooleanField(default=False)

    # Status
    preferred_payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='monthly')
    is_active = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    kyc_completed = models.BooleanField(default=False)

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

    # Add these fields to your Member model
    otp_enabled = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=100, blank=True, null=True)
    otp_backup_codes = models.JSONField(default=list, blank=True)
    otp_enabled_at = models.DateTimeField(null=True, blank=True)



# ============================================================
# LOAN PRODUCT MODEL
# ============================================================
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
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Annual interest rate %")
    term_months = models.IntegerField(default=12)
    term_days = models.IntegerField(default=360)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    requires_comaker = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    penalty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    penalty_start_days = models.IntegerField(default=360)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.display_name


# ============================================================
# LOAN APPLICATION MODEL
# ============================================================
class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('pending_staff_review', 'Pending Staff Review'),
        ('with_committee', 'With Committee'),
        ('line_approved', 'Line Approved'),
        ('pending_manager_approval', 'Pending Manager Approval'),
        ('manager_approved', 'Manager Approved'),
        ('active', 'Active'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
        ('ready_for_disbursement', 'Ready for Disbursement'),
        ('disbursed', 'Disbursed'),
    ]

    application_id = models.CharField(max_length=50, unique=True, blank=True)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='applications')
    co_maker = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='comaker_applications')
    applicant_user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.SET_NULL, null=True, blank=True)

    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_line = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    committee_approved_date = models.DateField(null=True, blank=True)
    committee_reduction_reason = models.TextField(blank=True)

    service_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cbu_retention = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=35)
    notarial_fee = models.DecimalField(max_digits=12, decimal_places=2, default=200)
    inspector_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    trade_fert = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ca_int = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_proceeds = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_payable = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    purpose = models.TextField()
    collateral_offered = models.TextField()
    mode_of_payment = models.CharField(max_length=20)
    loan_term = models.IntegerField(default=12)

    applicant_signature = models.TextField(blank=True, null=True)
    co_maker_signature = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_staff_review')
    staff_remarks = models.TextField(blank=True)
    committee_remarks = models.TextField(blank=True)
    manager_remarks = models.TextField(blank=True)

    valid_id_verified = models.BooleanField(default=False)
    valid_id_rejected = models.BooleanField(default=False)
    valid_id_rejection_reason = models.TextField(blank=True)
    collateral_verified = models.BooleanField(default=False)
    collateral_rejected = models.BooleanField(default=False)
    collateral_rejection_reason = models.TextField(blank=True)

    is_restructuring = models.BooleanField(default=False)
    restructured_from_loan = models.ForeignKey('Loan', on_delete=models.SET_NULL, null=True, blank=True)

    date_applied = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    form_data = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if not self.application_id:
            year = date.today().year
            last_app = LoanApplication.objects.filter(application_id__startswith=f'APCP-{year}').order_by(
                '-application_id').first()
            if last_app:
                last_num = int(last_app.application_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.application_id = f'APCP-{year}-{new_num:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.application_id


# ============================================================
# LOAN MODEL
# ============================================================
class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending_disbursement', 'Pending Disbursement'),
        ('active', 'Active'),
        ('overdue', 'Overdue'),
        ('restructured', 'Restructured'),
        ('paid', 'Paid'),
        ('defaulted', 'Defaulted'),
    ]

    # Payment Preference Choices
    PAYMENT_TYPE_CHOICES = [
        ('flexible', 'Flexible (Production-based)'),
        ('scheduled', 'Scheduled (Fixed Amortization)'),
    ]

    loan_number = models.CharField(max_length=50, unique=True, blank=True)
    loan_application_id = models.CharField(max_length=50, unique=True, blank=True)
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='funded_loan')
    borrower = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    co_maker = models.ForeignKey(Member, on_delete=models.SET_NULL, null=True, blank=True, related_name='comaker_loans')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.SET_NULL, null=True)

    # Loan Amounts
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)

    # Loan Terms
    term_months = models.IntegerField()
    term_days = models.IntegerField()

    # Dates
    disbursement_date = models.DateField()
    due_date = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)

    # Financial Calculations
    total_interest = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_penalty_incurred = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_payable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_proceeds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Loan Policy Settings
    penalty_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.02,
                                       help_text="Penalty rate per month (2% = 0.02)")
    penalty_start_days = models.IntegerField(default=361,
                                             help_text="Days after which penalty starts (361 = after 360 days)")

    # Interest Calculation
    daily_interest_rate = models.DecimalField(max_digits=10, decimal_places=8, default=0.00041667,
                                              help_text="Daily interest rate (annual_rate / 360)")
    estimated_monthly_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                                    help_text="Estimated payment for reference only")

    # Payment Preference
    payment_type = models.CharField(
        max_length=20,
        default='flexible',
        choices=PAYMENT_TYPE_CHOICES,
        help_text="Payment preference of the member"
    )

    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_disbursement')

    # Restructuring
    is_restructured = models.BooleanField(default=False)
    restructured_from_loan = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    no_cash_released = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    # User References
    approved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='approved_loans')
    disbursed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='disbursed_loans')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='created_loans')

    def save(self, *args, **kwargs):
        # Auto-generate loan_number if not provided
        if not self.loan_number:
            year = date.today().year
            last_loan = Loan.objects.filter(loan_number__startswith=f'LN-{year}').order_by('-loan_number').first()
            if last_loan:
                last_num = int(last_loan.loan_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.loan_number = f'LN-{year}-{new_num:04d}'

        # Auto-generate loan_application_id if not provided
        if not self.loan_application_id:
            year = date.today().year
            last_app = Loan.objects.filter(loan_application_id__startswith=f'LAPP-{year}').order_by(
                '-loan_application_id').first()
            if last_app:
                last_num = int(last_app.loan_application_id.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.loan_application_id = f'LAPP-{year}-{new_num:04d}'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.loan_number


# ============================================================
# PAYMENT SCHEDULE MODEL
# ============================================================
class PaymentSchedule(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('partial', 'Partially Paid'), ('paid', 'Paid')]

    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='schedules')
    schedule_number = models.IntegerField()
    due_date = models.DateField()
    principal_due = models.DecimalField(max_digits=12, decimal_places=2)
    interest_due = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_due = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['due_date']


# ============================================================
# PAYMENT MODEL
# ============================================================
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('pesada', 'Pesada'),
        ('quedan', 'Quedan'),
    ]
    STATUS_CHOICES = [('completed', 'Completed'), ('pending', 'Pending'), ('failed', 'Failed'), ('voided', 'Voided')]

    payment_number = models.CharField(max_length=50, unique=True, blank=True)
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='payments')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    schedule = models.ForeignKey(PaymentSchedule, on_delete=models.SET_NULL, null=True, blank=True)

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

    issued_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='issued_payments')
    posted_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='posted_payments')

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.payment_number:
            year = date.today().year
            last_payment = Payment.objects.filter(payment_number__startswith=f'PAY-{year}').order_by(
                '-payment_number').first()
            if last_payment:
                last_num = int(last_payment.payment_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.payment_number = f'PAY-{year}-{new_num:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.payment_number


# ============================================================
# PAYMENT RECEIPT MODEL
# ============================================================
class PaymentReceipt(models.Model):
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, related_name='receipt')
    member = models.ForeignKey(Member, on_delete=models.CASCADE)

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
            year = date.today().year
            last_receipt = PaymentReceipt.objects.filter(receipt_number__startswith=f'RCP-{year}').order_by(
                '-receipt_number').first()
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.receipt_number = f'RCP-{year}-{new_num:05d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


# ============================================================
# NOTIFICATION MODEL
# ============================================================
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('application', 'Application'),
        ('payment', 'Payment'),
        ('loan', 'Loan'),
        ('system', 'System'),
        ('alert', 'Alert'),
        ('approval', 'Approval'),
        ('committee', 'Committee'),
    ]

    recipient = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='notifications')
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


# ============================================================
# MEMBER DOCUMENTS
# ============================================================
class MemberDocument(models.Model):
    DOCUMENT_TYPES = [
        ('valid_id', 'Valid ID'),
        ('proof_income', 'Proof of Income'),
        ('collateral', 'Collateral Document'),
        ('others', 'Others'),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    document_number = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='member_documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - {self.get_document_type_display()}"


# ============================================================
# LOAN ATTACHMENTS
# ============================================================
class LoanAttachment(models.Model):
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='attachments')
    document = models.ForeignKey(MemberDocument, on_delete=models.CASCADE)
    is_reused = models.BooleanField(default=False)
    attached_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.loan_application.application_id}"


# ============================================================
# COMMITTEE DECISIONS
# ============================================================
class CommitteeDecision(models.Model):
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE,
                                         related_name='committee_decisions')
    committee_member = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True,
                                         limit_choices_to={'is_staff': True})
    approved_line_amount = models.DecimalField(max_digits=12, decimal_places=2)
    date_approved = models.DateField(auto_now_add=True)
    reduction_reason = models.TextField(blank=True)
    decision = models.CharField(max_length=20, choices=[('approved', 'Approved'), ('rejected', 'Rejected'),
                                                        ('revision', 'Needs Revision')])
    comments = models.TextField(blank=True)
    voted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Decision for {self.loan_application.application_id}"


# ============================================================
# AUDIT LOGS
# ============================================================
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
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


# ============================================================
# SYSTEM SETTINGS
# ============================================================
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
    updated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.setting_key} = {self.setting_value}"


# ============================================================
# PAYMENT REMINDER
# ============================================================
class PaymentReminder(models.Model):
    REMINDER_TYPES = [
        ('7_days', '7 Days Before Due'),
        ('3_days', '3 Days Before Due'),
        ('1_day', '1 Day Before Due'),
        ('due_date', 'Due Date'),
        ('overdue_7', '7 Days Overdue'),
        ('overdue_15', '15 Days Overdue'),
        ('overdue_30', '30 Days Overdue'),
    ]
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Reminder for {self.loan.loan_number} - {self.get_reminder_type_display()}"


class CommitteeVote(models.Model):
    """
    Model to store committee votes on loan applications.
    Committee members vote to approve, reject, or request revision.
    """
    VOTE_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('request_revision', 'Request Revision'),
    ]

    application = models.ForeignKey(
        'LoanApplication',
        on_delete=models.CASCADE,
        related_name='committee_votes'
    )
    committee_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='committee_votes'
    )
    vote = models.CharField(max_length=20, choices=VOTE_CHOICES)
    approved_line = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Approved loan amount (for approve votes only)"
    )
    reduction_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason if approved amount is less than requested"
    )
    reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection or revision request"
    )
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['application', 'committee_member']
        ordering = ['-voted_at']
        verbose_name = "Committee Vote"
        verbose_name_plural = "Committee Votes"

    def __str__(self):
        return f"{self.committee_member.username} - {self.application.application_id} - {self.vote}"

    def save(self, *args, **kwargs):
        # Clean text fields - convert 'None' string to empty string
        text_fields = [
            'middle_initial', 'nickname', 'spouse_name', 'farm_location',
            'adjacent_farm', 'other_loans', 'employer_name', 'employer_address',
            'business_kind', 'position', 'supervisor_name', 'previous_employer',
            'self_employed_firm', 'self_employed_address', 'self_employed_business_kind',
            'trade_reference', 'other_income_sources', 'bank_name', 'relationship_type',
            'previous_lender', 'previous_borrower_name'
        ]

        for field in text_fields:
            value = getattr(self, field, None)
            if value and (value == 'None' or value == 'null'):
                setattr(self, field, '')

        # Ensure middle_initial is max 1 character
        if self.middle_initial and len(self.middle_initial) > 1:
            self.middle_initial = self.middle_initial[0]

        super().save(*args, **kwargs)