import re

with open('admin_panel/templates/admin_panel/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the Payment Receipts link to point to Payments page (since receipts come from payments)
content = content.replace(
    '<a class="nav-link" href="{% url \'admin_panel:payment_receipts_list\' %}">',
    '<a class="nav-link" href="{% url \'admin_panel:payments_list\' %}">'
)

with open('admin_panel/templates/admin_panel/base.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated Payment Receipts link to redirect to Payments page')
