import os
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.files.base import ContentFile
from django.contrib.auth.models import User, Group
from main.models import (
    Member, LoanProduct, LoanApplication, Notification, 
    StaffProfile, PaymentSchedule, Loan
)


def create_dummy_image(filename, text, size=(400, 300)):
    """Create a dummy image for testing"""
    img = Image.new('RGB', size, color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([(0, 0), (size[0]-1, size[1]-1)], outline=(200, 200, 200), width=2)
    
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(((size[0] - text_width) // 2, (size[1] - text_height) // 2), text, fill=(0, 0, 0), font=font)
    
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=filename)


def create_dummy_pdf(filename, content):
    """Create a dummy PDF file for testing"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    c.drawString(100, height - 100, content)
    c.drawString(100, height - 120, "TOMPuCO COOPERATIVE")
    c.drawString(100, height - 140, "Sample Document for Testing")
    c.drawString(100, height - 160, f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
    
    c.save()
    return ContentFile(buffer.getvalue(), name=filename)


def create_ready_loan_sample():
    print("=" * 70)
    print("CREATING COMPLETE SAMPLE LOAN APPLICATION READY FOR DISBURSEMENT")
    print("=" * 70)
    
    # 1. Create Staff User
    print("\n📌 1. CREATING STAFF USER...")
    staff_user, created = User.objects.get_or_create(
        username='staff_maria',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria.santos@tompuco.com',
            'is_staff': True,
            'is_active': True
        }
    )
    if created:
        staff_user.set_password('staff123')
        staff_user.save()
        print(f"   ✅ Staff: staff_maria / staff123")
    else:
        print(f"   ℹ️ Staff user already exists")
    
    staff_profile, created = StaffProfile.objects.get_or_create(
        user=staff_user,
        defaults={
            'department': 'Loan Operations',
            'position': 'Senior Loan Officer',
            'phone_number': '09171234567',
            'employee_id': f'STF-{staff_user.id:05d}'
        }
    )
    
    # 2. Create Member User
    print("\n📌 2. CREATING MEMBER USER...")
    member_user, created = User.objects.get_or_create(
        username='juan_delacruz',
        defaults={
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'email': 'juan.delacruz@email.com',
            'is_active': True
        }
    )
    if created:
        member_user.set_password('member123')
        member_user.save()
        print(f"   ✅ Member: juan_delacruz / member123")
    else:
        print(f"   ℹ️ Member user already exists")
    
    # 3. Create Member Profile
    print("\n📌 3. CREATING COMPLETE MEMBER PROFILE...")
    
    signature_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAPoAAAD6CAYAAACI7Fo9AAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAZdEVYdFNvZnR3YXJlAHBhaW50Lm5ldCA0LjAuMTM0A1t6AAAAI0lEQVR4nO3BMQEAAADCoPVPbQhfoAAAAAAAAAAAAAAAAAAAAIDXASteAAEBXK/pAAAAAElFTkSuQmCC"
    
    member, created = Member.objects.get_or_create(
        user=member_user,
        defaults={
            'membership_number': f'M-{random.randint(10000, 99999)}',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'middle_initial': 'C',
            'nickname': 'Jun',
            'nationality': 'Filipino',
            'birthdate': datetime(1990, 5, 15).date(),
            'age': 34,
            'gender': 'M',
            'contact_number': '09123456789',
            'residence_address': '#123 Barangay San Isidro, Makati City, Negros Oriental',
            'spouse_name': 'Maria Dela Cruz',
            'num_dependents': 2,
            'farm_location': 'Barangay San Isidro, Makati City',
            'farm_owned_hectares': Decimal('2.5'),
            'farm_leased_hectares': Decimal('1.0'),
            'adjacent_farm': 'Barangay San Juan - owned by Pedro Santos',
            'area_planted': Decimal('3.5'),
            'new_plant': Decimal('1.0'),
            'ratoon_crops': Decimal('2.5'),
            'is_employee': False,
            'other_loans': 'Previous loan from CARD Bank - ₱30,000 (fully paid)',
            'monthly_income': Decimal('35000'),
            'other_income_sources': 'Sari-sari store - ₱5,000/month',
            'bank_name': 'Land Bank of the Philippines',
            'bank_account_type': 'Savings',
            'years_in_address': 15,
            'years_in_community': 20,
            'self_employed_firm': 'Dela Cruz Farm',
            'self_employed_address': '#123 Barangay San Isidro, Makati City',
            'self_employed_business_kind': 'Sugarcane Farming',
            'years_in_business': 15,
            'trade_reference': 'San Miguel Corporation',
            'real_estate_1': 'Agricultural land at Barangay San Isidro - 2.5 hectares',
            'real_estate_1_owner': 'Juan Dela Cruz',
            'real_estate_1_value': Decimal('850000'),
            'real_estate_1_mortgage': Decimal('0'),
            'preferred_payment_mode': 'monthly',
            'is_active': True,
            'kyc_completed': True,
            'signature': signature_data,
        }
    )
    
    print(f"   ✅ Member Profile Created:")
    print(f"      - Name: {member.last_name}, {member.first_name}")
    print(f"      - Membership #: {member.membership_number}")
    print(f"      - Monthly Income: ₱{member.monthly_income:,.2f}")
    
    # 4. Upload Valid ID
    print("\n📌 4. UPLOADING VALID ID DOCUMENT...")
    
    valid_id_image = create_dummy_image(
        'valid_id_sample.png',
        'PHILIPPINE NATIONAL ID\n\nName: JUAN DELA CRUZ\nID No: 1234-5678-9012-3456\nIssued: 2024-01-15'
    )
    member.uploaded_id = valid_id_image
    member.save()
    print(f"   ✅ Valid ID uploaded")
    
    # 5. Upload Collateral Document
    print("\n📌 5. UPLOADING COLLATERAL DOCUMENT...")
    
    collateral_content = """TCT NO. 12345
Transfer Certificate of Title

Lot No.: 1234
Location: Barangay San Isidro, Makati City
Area: 2.5 hectares
Registered Owner: Juan Dela Cruz

This document certifies that the above-named person is the registered owner of the described property.
Issued by: Registry of Deeds, Negros Oriental
Date: 2010-03-20"""
    
    collateral_pdf = create_dummy_pdf('collateral_tct_12345.pdf', collateral_content)
    member.collateral_document = collateral_pdf
    member.collateral_document_type = 'Land Title (TCT)'
    member.collateral_document_number = 'TCT-12345'
    member.collateral_issued_by = 'Registry of Deeds - Negros Oriental'
    member.collateral_issue_date = datetime(2010, 3, 20).date()
    member.collateral_property_description = '2.5 hectares agricultural land at Barangay San Isidro, Makati City'
    member.collateral_area = Decimal('2.5')
    member.collateral_is_verified = True
    member.save()
    print(f"   ✅ Collateral Document uploaded: TCT-12345 - 2.5 hectares")
    
    # 6. Create Loan Product
    print("\n📌 6. CREATING LOAN PRODUCT...")
    loan_product, created = LoanProduct.objects.get_or_create(
        name='APCP',
        defaults={
            'display_name': 'Agricultural Production Credit Program',
            'loan_type': 'APCP',
            'interest_rate': Decimal('20.00'),
            'term_months': 12,
            'term_days': 360,
            'min_amount': Decimal('10000'),
            'max_amount': Decimal('500000'),
            'requires_comaker': True,
            'is_active': True,
            'description': 'For agricultural production needs - sugarcane production'
        }
    )
    print(f"   ✅ Loan Product: {loan_product.display_name} - {loan_product.interest_rate}% per annum")
    
    # 7. Create Co-Maker
    print("\n📌 7. CREATING CO-MAKER PROFILE...")
    
    co_maker_user, created = User.objects.get_or_create(
        username='pedro_santos',
        defaults={
            'first_name': 'Pedro',
            'last_name': 'Santos',
            'email': 'pedro.santos@email.com',
            'is_active': True
        }
    )
    if created:
        co_maker_user.set_password('comaker123')
        co_maker_user.save()
        print(f"   ✅ Co-maker user created: pedro_santos / comaker123")
    
    co_maker, created = Member.objects.get_or_create(
        user=co_maker_user,
        defaults={
            'membership_number': f'M-{random.randint(10000, 99999)}',
            'first_name': 'Pedro',
            'last_name': 'Santos',
            'middle_initial': 'R',
            'nickname': 'Ped',
            'nationality': 'Filipino',
            'birthdate': datetime(1985, 8, 20).date(),
            'age': 39,
            'gender': 'M',
            'contact_number': '09123456788',
            'residence_address': '#456 Barangay San Juan, Makati City, Negros Oriental',
            'spouse_name': 'Luz Santos',
            'num_dependents': 3,
            'is_employee': True,
            'employer_name': 'San Miguel Corporation',
            'position': 'Production Supervisor',
            'monthly_salary': Decimal('45000'),
            'monthly_income': Decimal('45000'),
            'other_income_sources': 'Rental income - ₱8,000/month',
            'bank_name': 'BDO',
            'bank_account_type': 'Checking',
            'years_in_address': 10,
            'years_in_community': 25,
            'years_known_applicant': 15,
            'has_been_borrower': True,
            'previous_lender': 'BDO',
            'has_been_comaker': True,
            'previous_borrower_name': 'Juan Dela Cruz',
            'preferred_payment_mode': 'monthly',
            'is_active': True,
            'kyc_completed': True,
            'signature': signature_data,
        }
    )
    print(f"   ✅ Co-Maker Created:")
    print(f"      - Name: {co_maker.last_name}, {co_maker.first_name}")
    print(f"      - Membership #: {co_maker.membership_number}")
    
    # 8. Create Loan Application
    print("\n📌 8. CREATING LOAN APPLICATION (APPROVED STATUS)...")
    
    approved_line = Decimal('80000')
    requested_amount = Decimal('100000')
    interest_rate = Decimal('20')
    term = 12
    monthly_rate = (interest_rate / 100) / 12
    
    if monthly_rate > 0:
        monthly_payment = (approved_line * monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
    else:
        monthly_payment = approved_line / term
    
    total_payable = monthly_payment * term
    total_interest = total_payable - approved_line
    
    service_charge = approved_line * Decimal('0.03')
    cbu_retention = approved_line * Decimal('0.02')
    insurance = approved_line * Decimal('0.0132')
    service_fee = Decimal('35')
    notarial_fee = Decimal('200')
    inspector_fee = Decimal('500')
    
    total_deductions = service_charge + cbu_retention + insurance + service_fee + notarial_fee + inspector_fee
    net_proceeds = approved_line - total_deductions
    
    current_date = datetime.now().date()
    
    application, created = LoanApplication.objects.get_or_create(
        application_id='APCP-2026-READY-001',
        defaults={
            'member': member,
            'co_maker': co_maker,
            'applicant_user': member_user,
            'loan_product': loan_product,
            'requested_amount': requested_amount,
            'approved_line': approved_line,
            'committee_approved_date': current_date - timedelta(days=5),
            'committee_reduction_reason': 'Based on member\'s existing loan balance',
            'service_charge': service_charge,
            'cbu_retention': cbu_retention,
            'insurance_charge': insurance,
            'service_fee': service_fee,
            'notarial_fee': notarial_fee,
            'inspector_fee': inspector_fee,
            'total_deductions': total_deductions,
            'net_proceeds': net_proceeds,
            'interest_rate': interest_rate,
            'total_interest': total_interest,
            'monthly_payment': monthly_payment,
            'total_payable': total_payable,
            'purpose': 'FARM PRODUCTION - Purchase of agricultural inputs',
            'collateral_offered': '2.5 hectares agricultural land, TCT No. 12345',
            'mode_of_payment': 'monthly',
            'loan_term': term,
            'status': 'manager_approved',
            'staff_remarks': 'All documents verified',
            'committee_remarks': 'Approved line: ₱80,000',
            'manager_remarks': 'Approved for disbursement',
            'valid_id_verified': True,
            'collateral_verified': True,
            'created_at': current_date - timedelta(days=10),
            'date_applied': (current_date - timedelta(days=10)),
        }
    )
    
    print(f"   ✅ Application Created:")
    print(f"      - Application ID: {application.application_id}")
    print(f"      - Status: {application.status}")
    print(f"      - Net Proceeds: ₱{application.net_proceeds:,.2f}")
    
    # 9. Create Notification
    print("\n📌 9. CREATING NOTIFICATION...")
    notification, created = Notification.objects.get_or_create(
        recipient=staff_user,
        title='Application Ready for Loan Creation',
        defaults={
            'notification_type': 'application',
            'message': f'Application {application.application_id} is ready for loan creation.',
            'link': f'/staff/applications/{application.id}/review/',
            'is_read': False
        }
    )
    print(f"   ✅ Notification created")
    
    # 10. Final Summary
    print("\n" + "=" * 70)
    print("✅ SAMPLE LOAN APPLICATION READY FOR DISBURSEMENT!")
    print("=" * 70)
    print("\n🔐 LOGIN CREDENTIALS:")
    print(f"   Staff:   staff_maria / staff123")
    print(f"   Member:  juan_delacruz / member123")
    print(f"   Co-maker: pedro_santos / comaker123")
    print("\n📋 STAFF INSTRUCTIONS:")
    print(f"   1. Login as staff: staff_maria / staff123")
    print(f"   2. Go to: http://127.0.0.1:8000/staff/applications/")
    print(f"   3. Find application: {application.application_id}")
    print(f"   4. Click 'Review' then 'Create Loan & Disburse'")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    create_ready_loan_sample()
