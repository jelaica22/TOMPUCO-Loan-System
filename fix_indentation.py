import re

with open('staff/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and fix the indentation issue
lines = content.split('\n')
fixed_lines = []
for line in lines:
    # Remove any unexpected indentation at the beginning of lines with imports
    if line.strip().startswith('from main.models import') and line.startswith('    '):
        line = line.lstrip()
    fixed_lines.append(line)

content = '\n'.join(fixed_lines)

# Also ensure the payment API functions are properly indented
if 'def api_search_loan' in content:
    # The functions are already added, just need to ensure proper formatting
    pass

with open('staff/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Fixed indentation in staff/views.py')
