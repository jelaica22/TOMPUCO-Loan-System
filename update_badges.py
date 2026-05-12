import re

with open('admin_panel/templates/admin_panel/payments_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update badge display for Pesada and Quedan
badge_updates = [
    ('''{% elif payment.payment_method == 'bank_transfer' %}
                            <span class="badge-bank"><i class="bi bi-building"></i> Bank Transfer</span>''',
     '''{% elif payment.payment_method == 'pesada' %}
                            <span class="badge-bank"><i class="bi bi-scale"></i> Pesada</span>'''),
    ('''{% elif payment.payment_method == 'check' %}
                            <span class="badge-check"><i class="bi bi-check2-circle"></i> Check</span>''',
     '''{% elif payment.payment_method == 'quedan' %}
                            <span class="badge-check"><i class="bi bi-file-text"></i> Quedan</span>'''),
]

for old, new in badge_updates:
    if old in content:
        content = content.replace(old, new)

with open('admin_panel/templates/admin_panel/payments_list.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated badge displays for Pesada and Quedan')
