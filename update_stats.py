import re

with open('admin_panel/templates/admin_panel/payments_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update stats card labels
content = content.replace(
    '<div class="stat-card bank"><div class="stat-label">Bank Transfer</div>',
    '<div class="stat-card bank"><div class="stat-label">Pesada</div>'
)
content = content.replace(
    '<div class="stat-card check"><div class="stat-label">Check</div>',
    '<div class="stat-card check"><div class="stat-label">Quedan</div>'
)

with open('admin_panel/templates/admin_panel/payments_list.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ Updated stats card labels')
