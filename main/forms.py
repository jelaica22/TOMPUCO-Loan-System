from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from main.models import Member
from datetime import date
from django.contrib.auth.forms import AuthenticationForm
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox


class CustomLoginForm(AuthenticationForm):
    """Login form with reCAPTCHA protection"""
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Style your fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })


class MemberRegistrationForm(UserCreationForm):
    # Personal Information
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    middle_initial = forms.CharField(max_length=2, required=False)
    nickname = forms.CharField(max_length=50, required=False)
    nationality = forms.CharField(max_length=50, initial='Filipino', required=False)
    contact_number = forms.CharField(max_length=15, required=True)
    residence_address = forms.CharField(widget=forms.Textarea, required=True)
    spouse_name = forms.CharField(max_length=200, required=False)
    num_dependents = forms.IntegerField(min_value=0, required=False)

    # Farm Information
    farm_location = forms.CharField(max_length=200, required=False)
    farm_owned_hectares = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    farm_leased_hectares = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    area_planted = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    new_plant = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    ratoon_crops = forms.DecimalField(max_digits=10, decimal_places=2, required=False)
    adjacent_farm = forms.CharField(max_length=200, required=False)

    # Employment
    employer_tradename = forms.CharField(max_length=200, required=False)
    employer_address = forms.CharField(max_length=200, required=False)
    business_kind = forms.CharField(max_length=100, required=False)
    position = forms.CharField(max_length=100, required=False)
    years_with_employer = forms.IntegerField(required=False)
    supervisor_name = forms.CharField(max_length=100, required=False)
    previous_employer = forms.CharField(max_length=200, required=False)
    monthly_income = forms.DecimalField(max_digits=12, decimal_places=2, required=False)
    other_income_sources = forms.CharField(max_length=200, required=False)

    # Co-maker Info
    years_in_address = forms.IntegerField(required=False)
    years_in_community = forms.IntegerField(required=False)
    bank_name = forms.CharField(max_length=100, required=False)
    bank_account_type = forms.CharField(max_length=20, required=False)
    years_known_applicant = forms.IntegerField(required=False)
    is_related_to_applicant = forms.BooleanField(required=False)
    relationship_type = forms.CharField(max_length=50, required=False)
    has_been_borrower = forms.BooleanField(required=False)
    previous_lender = forms.CharField(max_length=200, required=False)
    has_been_comaker = forms.BooleanField(required=False)
    previous_borrower_name = forms.CharField(max_length=200, required=False)

    # Self Employment
    self_employed_firm = forms.CharField(max_length=200, required=False)
    self_employed_address = forms.CharField(max_length=200, required=False)
    self_employed_business_kind = forms.CharField(max_length=100, required=False)
    years_in_business = forms.IntegerField(required=False)
    trade_reference = forms.CharField(max_length=200, required=False)

    # Loan History
    other_loans = forms.CharField(widget=forms.Textarea, required=False)

    # Account
    username = forms.CharField(max_length=150, required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)
    birthdate = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=True)

    # ✅ ADD THIS reCAPTCHA FIELD
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            # Create Member profile with ALL fields
            member = Member.objects.create(
                user=user,
                # Personal
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                middle_initial=self.cleaned_data.get('middle_initial', ''),
                nickname=self.cleaned_data.get('nickname', ''),
                nationality=self.cleaned_data.get('nationality', 'Filipino'),
                birthdate=self.cleaned_data['birthdate'],
                gender=self.cleaned_data['gender'],
                contact_number=self.cleaned_data['contact_number'],
                residence_address=self.cleaned_data['residence_address'],
                spouse_name=self.cleaned_data.get('spouse_name', ''),
                num_dependents=self.cleaned_data.get('num_dependents', 0),

                # Farm
                farm_location=self.cleaned_data.get('farm_location', ''),
                farm_owned_hectares=self.cleaned_data.get('farm_owned_hectares', 0),
                farm_leased_hectares=self.cleaned_data.get('farm_leased_hectares', 0),
                area_planted=self.cleaned_data.get('area_planted', 0),
                new_plant=self.cleaned_data.get('new_plant', 0),
                ratoon_crops=self.cleaned_data.get('ratoon_crops', 0),
                adjacent_farm=self.cleaned_data.get('adjacent_farm', ''),

                # Employment
                employer_name=self.cleaned_data.get('employer_tradename', ''),
                position=self.cleaned_data.get('position', ''),
                monthly_income=self.cleaned_data.get('monthly_income', 0),
                other_income_sources=self.cleaned_data.get('other_income_sources', ''),

                # Co-maker
                years_in_address=self.cleaned_data.get('years_in_address', 0),
                years_in_community=self.cleaned_data.get('years_in_community', 0),
                bank_name=self.cleaned_data.get('bank_name', ''),
                bank_account_type=self.cleaned_data.get('bank_account_type', ''),
                years_known_applicant=self.cleaned_data.get('years_known_applicant', 0),
                is_related_to_applicant=self.cleaned_data.get('is_related_to_applicant', False),
                relationship_type=self.cleaned_data.get('relationship_type', ''),
                has_been_borrower=self.cleaned_data.get('has_been_borrower', False),
                previous_lender=self.cleaned_data.get('previous_lender', ''),
                has_been_comaker=self.cleaned_data.get('has_been_comaker', False),
                previous_borrower_name=self.cleaned_data.get('previous_borrower_name', ''),

                # Self Employment
                self_employed_firm=self.cleaned_data.get('self_employed_firm', ''),
                self_employed_address=self.cleaned_data.get('self_employed_address', ''),
                self_employed_business_kind=self.cleaned_data.get('self_employed_business_kind', ''),
                years_in_business=self.cleaned_data.get('years_in_business', 0),
                trade_reference=self.cleaned_data.get('trade_reference', ''),

                # Loan History
                other_loans=self.cleaned_data.get('other_loans', ''),

                # Status
                is_active=True,
                kyc_completed=True
            )
        return user


# Add these imports at the top of your forms.py
from decimal import Decimal
from .models import LoanApplication, LoanProduct


# Add these classes at the end of your forms.py file

class LoanApplicationForm(forms.ModelForm):
    """Form for loan application with validation"""
    requested_amount = forms.DecimalField(
        min_value=1000,
        max_value=5000000,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    purpose = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    collateral_offered = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        required=False
    )
    mode_of_payment = forms.ChoiceField(
        choices=[('monthly', 'Monthly'), ('weekly', 'Weekly')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    loan_term = forms.IntegerField(
        min_value=1,
        max_value=60,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    co_maker_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter co-maker membership number'})
    )
    loan_product_id = forms.ModelChoiceField(
        queryset=LoanProduct.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = LoanApplication
        fields = ['requested_amount', 'purpose', 'collateral_offered', 'mode_of_payment', 'loan_term']

    def clean_requested_amount(self):
        amount = self.cleaned_data.get('requested_amount')
        product_id = self.data.get('loan_product_id')
        if product_id:
            try:
                product = LoanProduct.objects.get(id=product_id)
                if amount < product.min_amount:
                    raise forms.ValidationError(f'Minimum amount for this product is ₱{product.min_amount:,.2f}')
                if amount > product.max_amount:
                    raise forms.ValidationError(f'Maximum amount for this product is ₱{product.max_amount:,.2f}')
            except LoanProduct.DoesNotExist:
                pass
        return amount

    def clean_loan_term(self):
        term = self.cleaned_data.get('loan_term')
        if term < 1 or term > 60:
            raise forms.ValidationError('Loan term must be between 1 and 60 months.')
        return term


class CoMakerForm(forms.Form):
    """Form for co-maker validation"""
    membership_number = forms.CharField(
        max_length=50,
        required=True,
        label='Co-maker Membership Number',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter membership number'})
    )

    def clean_membership_number(self):
        membership_number = self.cleaned_data.get('membership_number')
        try:
            co_maker = Member.objects.get(membership_number=membership_number, is_active=True)
            return co_maker
        except Member.DoesNotExist:
            raise forms.ValidationError('Invalid membership number. Please enter a valid co-maker ID.')