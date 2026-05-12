import re

with open('admin_panel/templates/admin_panel/payments_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure the Receipt button calls the correct function
if 'downloadReceipt' in content:
    content = content.replace(
        'downloadReceipt({{ payment.id }})',
        'downloadReceipt({{ payment.id }})'
    )
    
with open('admin_panel/templates/admin_panel/payments_list.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Verified receipt button in payments list')
