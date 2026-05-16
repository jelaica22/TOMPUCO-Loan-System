from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.conf import settings
from decimal import Decimal
from .models import Member, LoanApplication, LoanProduct


class CustomLoginForm(AuthenticationForm):
    """Login form with conditional reCAPTCHA"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'id': 'username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'id': 'password'
        })


class MemberRegistrationForm(UserCreationForm):
    # Personal Information - Required fields
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'email'}))
    first_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    middle_initial = forms.CharField(max_length=2, required=False,
                                     widget=forms.TextInput(attrs={'class': 'form-control'}))
    nickname = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    nationality = forms.CharField(max_length=50, initial='Filipino', required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))

    civil_status = forms.ChoiceField(
        choices=[('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'),
                 ('widowed', 'Widowed'), ('separated', 'Legally Separated')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'civil_status'})
    )

    birthdate = forms.DateField(required=True, widget=forms.DateInput(
        attrs={'class': 'form-control', 'type': 'date', 'id': 'birthdate'}))
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')], required=True,
                               widget=forms.Select(attrs={'class': 'form-select'}))

    contact_number = forms.CharField(max_length=11, required=True, widget=forms.TextInput(
        attrs={'class': 'form-control', 'id': 'contact_number', 'placeholder': '09123456789'}))
    residence_address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
                                        required=True)
    spouse_name = forms.CharField(max_length=200, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'spouse_name'}))
    num_dependents = forms.IntegerField(min_value=0, required=False, initial=0,
                                        widget=forms.NumberInput(attrs={'class': 'form-control'}))

    # Farm Information (Optional - can be N/A)
    farm_location = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'N/A if none'}))
    farm_owned_hectares = forms.DecimalField(max_digits=10, decimal_places=2, required=False, initial=0,
                                             widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    farm_leased_hectares = forms.DecimalField(max_digits=10, decimal_places=2, required=False, initial=0,
                                              widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    area_planted = forms.DecimalField(max_digits=10, decimal_places=2, required=False, initial=0,
                                      widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    new_plant = forms.DecimalField(max_digits=10, decimal_places=2, required=False, initial=0,
                                   widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    ratoon_crops = forms.DecimalField(max_digits=10, decimal_places=2, required=False, initial=0,
                                      widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    adjacent_farm = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'N/A if none'}))

    # Income Information
    monthly_income = forms.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=0,
                                        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1000'}))
    other_income_sources = forms.CharField(max_length=200, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'N/A if none'}))
    other_loans = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Write "None" if none'}),
        required=False)

    # Employee specific fields (for employee members)
    position = forms.CharField(max_length=100, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'N/A if not applicable'}))
    employee_id = forms.CharField(max_length=50, required=False, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'N/A if not applicable'}))
    date_hired = forms.DateField(required=False,
                                 widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    # Account fields
    username = forms.CharField(max_length=150, required=True,
                               widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password1'}),
                                required=True)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password2'}),
                                required=True)

    # User type (Regular Member or Employee Member)
    user_type = forms.ChoiceField(
        choices=[('member', '📋 Regular Member'), ('employee', '⭐ Employee Member')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'user_type'})
    )

    # Terms and Conditions
    terms = forms.BooleanField(required=True,
                               widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'terms'}))
    dataPrivacy = forms.BooleanField(required=True, widget=forms.CheckboxInput(
        attrs={'class': 'form-check-input', 'id': 'dataPrivacy'}))
    agreeTerms = forms.BooleanField(required=True,
                                    widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'agreeTerms'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already registered.')
        return email

    def clean_contact_number(self):
        contact = self.cleaned_data.get('contact_number')
        # Remove any non-digit characters
        digits = ''.join(filter(str.isdigit, contact))
        if len(digits) != 11:
            raise forms.ValidationError('Contact number must be exactly 11 digits.')
        return digits

    def clean_monthly_income(self):
        income = self.cleaned_data.get('monthly_income')
        if income and income <= 0:
            raise forms.ValidationError('Monthly income must be greater than 0.')
        return income

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        if not any(c.isupper() for c in password):
            raise forms.ValidationError('Password must contain at least one uppercase letter.')
        if not any(c.islower() for c in password):
            raise forms.ValidationError('Password must contain at least one lowercase letter.')
        if not any(c.isdigit() for c in password):
            raise forms.ValidationError('Password must contain at least one number.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()

            # Handle "N/A" values for optional fields
            def clean_optional(value):
                if value in ['N/A', 'n/a', 'N/a', '']:
                    return None
                return value

            member = Member.objects.create(
                user=user,
                membership_number=f"M-{user.id:05d}",
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                middle_initial=clean_optional(self.cleaned_data.get('middle_initial', '')),
                nickname=clean_optional(self.cleaned_data.get('nickname', '')),
                nationality=self.cleaned_data.get('nationality', 'Filipino'),
                civil_status=self.cleaned_data.get('civil_status', 'single'),
                birthdate=self.cleaned_data['birthdate'],
                gender=self.cleaned_data['gender'],
                contact_number=self.cleaned_data['contact_number'],
                residence_address=self.cleaned_data['residence_address'],
                spouse_name=clean_optional(self.cleaned_data.get('spouse_name', '')),
                num_dependents=self.cleaned_data.get('num_dependents', 0),
                farm_location=clean_optional(self.cleaned_data.get('farm_location', '')),
                farm_owned_hectares=self.cleaned_data.get('farm_owned_hectares', 0),
                farm_leased_hectares=self.cleaned_data.get('farm_leased_hectares', 0),
                area_planted=self.cleaned_data.get('area_planted', 0),
                new_plant=self.cleaned_data.get('new_plant', 0),
                ratoon_crops=self.cleaned_data.get('ratoon_crops', 0),
                adjacent_farm=clean_optional(self.cleaned_data.get('adjacent_farm', '')),
                monthly_income=self.cleaned_data['monthly_income'],
                other_income_sources=clean_optional(self.cleaned_data.get('other_income_sources', '')),
                other_loans=clean_optional(self.cleaned_data.get('other_loans', '')),
                employment_status=self.cleaned_data.get('user_type', 'member'),
                position=clean_optional(self.cleaned_data.get('position', '')),
                employee_id=clean_optional(self.cleaned_data.get('employee_id', '')),
                date_hired=self.cleaned_data.get('date_hired'),
                salary_loan_eligible=(self.cleaned_data.get('user_type') == 'employee'),
                verification_status='pending',
                account_status='pending',
                is_active=False,
            )

            # Update membership number with actual member ID
            member.membership_number = f"M-{member.id:05d}"
            member.save()

        return user


class LoanApplicationForm(forms.ModelForm):
    """Form for loan application with validation"""

    requested_amount = forms.DecimalField(
        min_value=1000,
        max_value=5000000,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'requested_amount'})
    )
    purpose = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'purpose'}),
        required=True
    )
    collateral_offered = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'id': 'collateral'}),
        required=False
    )
    mode_of_payment = forms.ChoiceField(
        choices=[('monthly', 'Monthly'), ('weekly', 'Weekly'), ('quarterly', 'Quarterly'),
                 ('harvest', 'Harvest-based')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'payment_mode'})
    )
    loan_term = forms.IntegerField(
        min_value=1,
        max_value=60,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'loan_term'})
    )
    co_maker_id = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'id': 'co_maker_id', 'placeholder': 'Enter co-maker membership number'})
    )
    loan_product_id = forms.ModelChoiceField(
        queryset=LoanProduct.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'loan_type'})
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
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'id': 'comaker_search', 'placeholder': 'Enter membership number'})
    )

    def clean_membership_number(self):
        membership_number = self.cleaned_data.get('membership_number')
        try:
            co_maker = Member.objects.get(membership_number=membership_number, is_active=True)
            return co_maker
        except Member.DoesNotExist:
            raise forms.ValidationError('Invalid membership number. Please enter a valid co-maker ID.')