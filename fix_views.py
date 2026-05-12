import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Comment out the problematic imports and replace with placeholder data
lines = content.split('\n')
new_lines = []
skip_next = False

for line in lines:
    # Skip lines that try to import missing models
    if 'from main.models import MemberDocument' in line:
        new_lines.append('    # from main.models import MemberDocument  # Model not yet created')
        continue
    if 'from main.models import LoanAttachment' in line:
        new_lines.append('    # from main.models import LoanAttachment  # Model not yet created')
        continue
    if 'from main.models import PaymentReceipt' in line:
        new_lines.append('    # from main.models import PaymentReceipt  # Model not yet created')
        continue
    if 'from main.models import CommitteeDecision' in line:
        new_lines.append('    # from main.models import CommitteeDecision  # Model not yet created')
        continue
    if 'from main.models import AuditLog' in line:
        new_lines.append('    # from main.models import AuditLog  # Model not yet created')
        continue
    if 'from main.models import SystemSetting' in line:
        new_lines.append('    # from main.models import SystemSetting  # Model not yet created')
        continue
    
    # Skip the actual object queries and replace with empty lists
    if 'MemberDocument.objects.all()' in line:
        new_lines.append('    documents = []  # TODO: Create MemberDocument model')
        continue
    if 'LoanAttachment.objects.all()' in line:
        new_lines.append('    attachments = []  # TODO: Create LoanAttachment model')
        continue
    if 'PaymentReceipt.objects.all()' in line:
        new_lines.append('    receipts = []  # TODO: Create PaymentReceipt model')
        continue
    if 'CommitteeDecision.objects.all()' in line:
        new_lines.append('    decisions = []  # TODO: Create CommitteeDecision model')
        continue
    if 'AuditLog.objects.all()' in line:
        new_lines.append('    logs = []  # TODO: Create AuditLog model')
        continue
    if 'SystemSetting.objects.all()' in line:
        new_lines.append('    settings = []  # TODO: Create SystemSetting model')
        continue
    
    new_lines.append(line)

with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print('✓ Updated admin_panel/views.py')
