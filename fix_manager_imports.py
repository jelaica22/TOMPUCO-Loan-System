import re

with open('manager/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Payment import
if 'from main.models import' in content:
    content = content.replace(
        'from main.models import LoanApplication, Loan, CommitteeDecision, AuditLog, Member',
        'from main.models import LoanApplication, Loan, CommitteeDecision, AuditLog, Member, Payment'
    )
    with open('manager/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added Payment import to manager/views.py')
