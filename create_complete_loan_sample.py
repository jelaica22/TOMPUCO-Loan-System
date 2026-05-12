import os
import django
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
from io import BytesIO
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tompuco.settings')
django.setup()

from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from main.models import (
    Member, LoanProduct, LoanApplication, Notification, StaffProfile,
    LoanDocument, Signature, VerificationChecklist, Disbursement
)

def create_complete_loan_sample():
    print("=" * 70)
    print("CREATING COMPLETE LOAN APPLICATION WITH ALL DOCUMENTS")
    print("=" * 70)

    # 1. Create Staff User
    print("\n1. Creating Staff User...")
    staff_user, created = User.objects.get_or_create(
        username='staff_maria',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria@tompuco.com',
            'is_staff': True,
            'is_active': True
        }
    )
    if created:
        staff_user.set_password('staff123')
        staff_user.save()
        print("   ✓ Staff created: staff_maria / staff123")
    else:
        print("   ✓ Staff already exists")

    # Create Staff Profile
    staff_profile, created = StaffProfile.objects.get_or_create(
        user=staff_user,
        defaults={
            'position': 'Loan Manager',
            'department': 'Loans',
            'employee_id': f'EMP-{random.randint(1000, 9999)}'
        }
    )

    # 2. Create Member User
    print("\n2. Creating Member User...")
    member_user, created = User.objects.get_or_create(
        username='juan_delacruz',
        defaults={
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'email': 'juan@email.com',
            'is_active': True
        }
    )
    if created:
        member_user.set_password('member123')
        member_user.save()
        print("   ✓ Member created: juan_delacruz / member123")
    else:
        print("   ✓ Member already exists")

    # 3. Create Member Profile with complete info
    print("\n3. Creating Complete Member Profile...")
    member, created = Member.objects.update_or_create(
        user=member_user,
        defaults={
            'membership_number': f'M-{random.randint(10000, 99999)}',
            'first_name': 'Juan',
            'last_name': 'Dela Cruz',
            'middle_initial': 'C',
            'nickname': 'Juancho',
            'nationality': 'Filipino',
            'birthdate': date(1990, 5, 15),
            'age': 35,
            'gender': 'Male',
            'contact_number': '09123456789',
            'residence_address': '123 Barangay San Isidro, Makati City',
            'spouse_name': 'N/A',
            'number_of_dependents': 0,
            'monthly_income': Decimal('35000'),
            'other_income': Decimal('0'),
            'employment_status': 'Not Employee',
            'employer_name': 'N/A',
            'position': 'N/A',
            'years_with_employer': 0,
            'farm_location': 'N/A',
            'farm_owned_hectares': Decimal('0'),
            'farm_leased_hectares': Decimal('0'),
            'adjacent_farm': 'N/A',
            'area_planted_hectares': Decimal('0'),
            'new_plant_hectares': Decimal('0'),
            'ratoon_crops_hectares': Decimal('0'),
            'other_loans': 'None',
            'is_active': True
        }
    )
    print(f"   ✓ Member Profile: {member.membership_number} - {member.first_name} {member.last_name}")

    # 4. Create Co-maker
    print("\n4. Creating Co-maker...")
    comaker_user, created = User.objects.get_or_create(
        username='maria_santos',
        defaults={
            'first_name': 'Maria',
            'last_name': 'Santos',
            'email': 'maria.santos@email.com',
            'is_active': True
        }
    )
    if created:
        comaker_user.set_password('comaker123')
        comaker_user.save()
        print("   ✓ Co-maker created: maria_santos / comaker123")
    else:
        print("   ✓ Co-maker already exists")

    comaker, created = Member.objects.update_or_create(
        user=comaker_user,
        defaults={
            'membership_number': f'M-{random.randint(10000, 99999)}',
            'first_name': 'Maria',
            'last_name': 'Santos',
            'contact_number': '09123456788',
            'residence_address': '456 Barangay San Juan, Makati City',
            'monthly_income': Decimal('45000'),
            'is_active': True
        }
    )
    print(f"   ✓ Co-maker Profile: {comaker.membership_number}")

    # 5. Create Loan Product
    print("\n5. Creating Loan Product...")
    product, created = LoanProduct.objects.get_or_create(
        name='APCP',
        defaults={
            'display_name': 'Agricultural Production Credit Program',
            'interest_rate': Decimal('20'),
            'term_months': 12,
            'min_amount': Decimal('10000'),
            'max_amount': Decimal('500000'),
            'is_active': True
        }
    )
    print(f"   ✓ Loan Product: {product.display_name}")

    # 6. Create Loan Application (COMPLETE)
    print("\n6. Creating Complete Loan Application...")
    
    requested_amount = Decimal('47424')
    approved_line = Decimal('47424')
    interest_rate = Decimal('20')
    term_months = 12
    term_days = 360
    
    # Calculate monthly payment (simplified amortization)
    monthly_interest = (interest_rate / Decimal('100')) / Decimal('12')
    monthly_payment = (approved_line * monthly_interest * (1 + monthly_interest) ** term_months) / ((1 + monthly_interest) ** term_months - 1)
    monthly_payment = monthly_payment.quantize(Decimal('0.01'))
    
    total_interest = (monthly_payment * term_months) - approved_line
    total_payable = approved_line + total_interest
    
    # Calculate deductions
    service_charge = approved_line * Decimal('0.03')
    cbu_retention = approved_line * Decimal('0.02')
    insurance_charge = approved_line * Decimal('0.0132')
    service_fee = Decimal('35')
    notarial_fee = Decimal('200')
    total_deductions = service_charge + cbu_retention + insurance_charge + service_fee + notarial_fee
    net_proceeds = approved_line - total_deductions
    
    # Calculate dates
    disbursement_date = date(2026, 5, 5)
    due_date = disbursement_date + timedelta(days=term_days)
    
    app, created = LoanApplication.objects.update_or_create(
        application_id='APCP-2026-1003',
        defaults={
            'member': member,
            'co_maker': comaker,
            'applicant_user': member_user,
            'loan_product': product,
            'requested_amount': requested_amount,
            'approved_line': approved_line,
            'service_charge': service_charge,
            'cbu_retention': cbu_retention,
            'insurance_charge': insurance_charge,
            'service_fee': service_fee,
            'notarial_fee': notarial_fee,
            'total_deductions': total_deductions,
            'net_proceeds': net_proceeds,
            'interest_rate': interest_rate,
            'loan_term': term_months,
            'loan_term_days': term_days,
            'monthly_payment': monthly_payment,
            'total_interest': total_interest,
            'total_payable': total_payable,
            'purpose': 'Emergency fund',
            'collateral_offered': 'Personal property',
            'mode_of_payment': 'MONTHLY',
            'status': 'manager_approved',
            'date_applied': date(2026, 5, 4),
            'valid_id_verified': True,
            'collateral_verified': True,
            'co_maker_verified': True,
            'promissory_note_verified': True,
            'disclosure_statement_verified': True,
            'all_documents_received': True
        }
    )
    print(f"   ✓ Application: {app.application_id}")
    print(f"   ✓ Status: {app.status}")
    print(f"   ✓ Approved Line: ₱{approved_line:,.2f}")
    print(f"   ✓ Monthly Payment: ₱{monthly_payment:,.2f}")
    print(f"   ✓ Net Proceeds: ₱{net_proceeds:,.2f}")

    # 7. Create Signatures
    print("\n7. Creating Signatures...")
    
    signature_fields = [
        ('borrower_signature', member_user, True),
        ('comaker_signature', comaker_user, True),
        ('spouse_signature', member_user, False),  # No spouse
        ('witness_signature', staff_user, True)
    ]
    
    for field_name, signer, is_signed in signature_fields:
        sig, created = Signature.objects.get_or_create(
            loan_application=app,
            signature_type=field_name,
            defaults={
                'signed_by': signer,
                'signed_at': timezone.now() if is_signed else None,
                'ip_address': '127.0.0.1',
                'is_signed': is_signed
            }
        )
        if created:
            print(f"   ✓ {field_name.replace('_', ' ').title()} created")

    # 8. Create Verification Checklist
    print("\n8. Creating Verification Checklist...")
    checklist, created = VerificationChecklist.objects.get_or_create(
        loan_application=app,
        defaults={
            'valid_id_verified': True,
            'valid_id_verified_by': staff_user,
            'valid_id_verified_at': timezone.now(),
            'collateral_verified': True,
            'collateral_verified_by': staff_user,
            'collateral_verified_at': timezone.now(),
            'comaker_verified': True,
            'comaker_verified_by': staff_user,
            'comaker_verified_at': timezone.now(),
            'promissory_note_verified': True,
            'promissory_note_verified_by': staff_user,
            'promissory_note_verified_at': timezone.now(),
            'disclosure_statement_verified': True,
            'disclosure_statement_verified_by': staff_user,
            'disclosure_statement_verified_at': timezone.now(),
            'all_documents_received': True,
            'documents_received_by': staff_user,
            'documents_received_at': timezone.now(),
            'verification_completed': True,
            'verification_completed_by': staff_user,
            'verification_completed_at': timezone.now()
        }
    )
    print("   ✓ All verifications completed")

    # 9. Create Documents
    print("\n9. Creating Loan Documents...")
    
    # Create a dummy PDF content
    dummy_pdf = BytesIO()
    dummy_pdf.write(b'%PDF-1.4\n%Test PDF content for loan document\n')
    dummy_pdf.write(b'1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
    dummy_pdf.seek(0)
    
    documents = [
        ('valid_id', 'valid_id_juan_delacruz.pdf'),
        ('collateral', 'collateral_personal_property.pdf'),
        ('promissory_note', 'promissory_note_APCP-2026-1003.pdf'),
        ('disclosure_statement', 'disclosure_statement_APCP-2026-1003.pdf')
    ]
    
    for doc_type, filename in documents:
        doc, created = LoanDocument.objects.get_or_create(
            loan_application=app,
            document_type=doc_type,
            defaults={
                'file': ContentFile(dummy_pdf.getvalue(), name=filename),
                'uploaded_by': staff_user,
                'uploaded_at': timezone.now(),
                'is_verified': True,
                'verified_by': staff_user,
                'verified_at': timezone.now()
            }
        )
        if created:
            print(f"   ✓ {doc_type.replace('_', ' ').title()} uploaded and verified")
        dummy_pdf.seek(0)

    # 10. Create Disbursement Record
    print("\n10. Creating Disbursement Record...")
    disbursement, created = Disbursement.objects.get_or_create(
        loan_application=app,
        defaults={
            'disbursement_date': disbursement_date,
            'due_date': due_date,
            'amount': net_proceeds,
            'status': 'completed',
            'released_by': staff_user,
            'released_at': timezone.now(),
            'reference_number': f'DISB-{app.application_id}',
            'payment_method': 'Bank Transfer',
            'bank_name': 'Land Bank of the Philippines',
            'account_number': '1234-5678-9012',
            'notes': 'Loan proceeds released to member account'
        }
    )
    print(f"   ✓ Disbursement scheduled: {disbursement_date}")
    print(f"   ✓ Due date: {due_date}")
    print(f"   ✓ Amount: ₱{net_proceeds:,.2f}")

    # 11. Create Notification for Staff
    print("\n11. Creating Notifications...")
    notification, created = Notification.objects.get_or_create(
        user=staff_user,
        title='Complete Loan Application Ready',
        message=f'Loan application {app.application_id} for {member.first_name} {member.last_name} is complete and ready for disbursement. All documents and verifications are in order.',
        defaults={
            'notification_type': 'success',
            'is_read': False,
            'created_at': timezone.now()
        }
    )
    print("   ✓ Notification sent to staff")

    # 12. Summary
    print("\n" + "=" * 70)
    print("✅ COMPLETE LOAN APPLICATION CREATED SUCCESSFULLY!")
    print("=" * 70)
    
    print("\n📋 LOAN SUMMARY:")
    print(f"   Application ID: {app.application_id}")
    print(f"   Member: {member.first_name} {member.last_name}")
    print(f"   Co-maker: {comaker.first_name} {comaker.last_name}")
    print(f"   Requested Amount: ₱{requested_amount:,.2f}")
    print(f"   Approved Line: ₱{approved_line:,.2f}")
    print(f"   Net Proceeds: ₱{net_proceeds:,.2f}")
    print(f"   Monthly Payment: ₱{monthly_payment:,.2f}")
    print(f"   Total Interest: ₱{total_interest:,.2f}")
    print(f"   Total Payable: ₱{total_payable:,.2f}")
    print(f"   Disbursement Date: {disbursement_date}")
    print(f"   Due Date: {due_date}")
    
    print("\n📄 DOCUMENTS COMPLETED:")
    print("   ✓ Valid ID (Uploaded & Verified)")
    print("   ✓ Collateral Document (Uploaded & Verified)")
    print("   ✓ Promissory Note (Generated & Verified)")
    print("   ✓ Disclosure Statement (Generated & Verified)")
    
    print("\n✓ VERIFICATIONS COMPLETED:")
    print("   ✓ Valid ID Verified")
    print("   ✓ Collateral Verified")
    print("   ✓ Co-Maker Assigned and Verified")
    print("   ✓ Promissory Note Verified")
    print("   ✓ Disclosure Statement Verified")
    print("   ✓ All Documents Received")
    
    print("\n✍️ SIGNATURES COMPLETED:")
    print("   ✓ Borrower Signature")
    print("   ✓ Co-Maker Signature")
    print("   ✓ Witness Signature")
    print("   ✗ Spouse Signature (N/A - No spouse)")
    
    print("\n🔐 LOGIN CREDENTIALS:")
    print("   Staff:   staff_maria / staff123")
    print("   Member:  juan_delacruz / member123")
    print("   Co-maker: maria_santos / comaker123")
    
    print("\n📋 GO TO:")
    print("   Staff Dashboard: http://127.0.0.1:8000/staff/applications/")
    print(f"   View Application: http://127.0.0.1:8000/staff/application/{app.id}/")
    
    print("\n💰 DISBURSEMENT INFORMATION:")
    print(f"   Disbursement Date: {disbursement_date}")
    print(f"   Due Date (360 days after): {due_date}")
    print(f"   Penalty Rate: 2% per month on remaining balance after due date")
    print(f"   Grace Period: 360 days (No penalty for first {term_days} days)")
    
    print("\n" + "=" * 70)
    print("🎉 LOAN APPLICATION IS 100% COMPLETE AND READY FOR DISBURSEMENT!")
    print("=" * 70)

if __name__ == '__main__':
    create_complete_loan_sample()