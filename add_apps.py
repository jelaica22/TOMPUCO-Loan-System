with open('tompuco/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

apps_to_add = ['cashier', 'committee', 'manager']
modified = False

for app in apps_to_add:
    if f"'{app}'" not in content and f'"{app}"' not in content:
        # Find INSTALLED_APPS list and add the app
        import re
        pattern = r"(INSTALLED_APPS = \[)([^\]]*)(\])"
        def add_app(match):
            apps = match.group(2)
            return f"{match.group(1)}\n    '{app}',{apps}{match.group(3)}"
        content = re.sub(pattern, add_app, content, count=1)
        modified = True
        print(f'✓ Added {app} to INSTALLED_APPS')
    else:
        print(f'✓ {app} already in INSTALLED_APPS')

if modified:
    with open('tompuco/settings.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Settings saved!')
else:
    print('No changes needed')
