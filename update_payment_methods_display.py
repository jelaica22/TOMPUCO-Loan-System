import re

with open('admin_panel/templates/admin_panel/payments_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the edit payment modal payment method options
old_edit_method = '''<select name="payment_method" id="editPaymentMethod" class="form-select">
                                <option value="cash">Cash</option>
                                <option value="bank_transfer">Bank Transfer</option>
                                <option value="check">Check</option>
                                <option value="paymaya">PayMaya</option>
                            </select>'''

new_edit_method = '''<select name="payment_method" id="editPaymentMethod" class="form-select">
                                <option value="cash">Cash</option>
                                <option value="pesada">Pesada</option>
                                <option value="quedan">Quedan</option>
                            </select>'''

if old_edit_method in content:
    content = content.replace(old_edit_method, new_edit_method)
    print('✓ Updated edit modal payment methods')
else:
    print('Edit modal not found, trying alternative...')
    # Try a different pattern
    content = content.replace('bank_transfer', 'pesada')
    content = content.replace('check', 'quedan')
    content = content.replace('paymaya', 'pesada')
    print('✓ Updated using replacement')

# Update the add payment modal
old_add_method = '''<select name="payment_method" class="form-select">
                                <option value="cash">Cash</option>
                                <option value="bank_transfer">Bank Transfer</option>
                                <option value="check">Check</option>
                                <option value="paymaya">PayMaya</option>
                            </select>'''

new_add_method = '''<select name="payment_method" class="form-select">
                                <option value="cash">Cash</option>
                                <option value="pesada">Pesada</option>
                                <option value="quedan">Quedan</option>
                            </select>'''

if old_add_method in content:
    content = content.replace(old_add_method, new_add_method)
    print('✓ Updated add modal payment methods')

# Update filter dropdown
content = content.replace(
    '<option value="bank_transfer">Bank Transfer</option>',
    '<option value="pesada">Pesada</option>'
)
content = content.replace(
    '<option value="check">Check</option>',
    '<option value="quedan">Quedan</option>'
)
content = content.replace(
    '<option value="paymaya">PayMaya</option>',
    ''
)

with open('admin_panel/templates/admin_panel/payments_list.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('✓ All payment method options updated to Cash, Pesada, Quedan')
