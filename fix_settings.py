import re

with open('tompuco/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the middleware line
content = content.replace(
    'django.contrib.auth.middleware.AuthenticationMiddleware\n    \'main.middleware.RedirectManagerMiddleware\',',
    'django.contrib.auth.middleware.AuthenticationMiddleware,\n    \'main.middleware.RedirectManagerMiddleware\','
)

# Also ensure proper quotes
content = content.replace(
    "'django.contrib.auth.middleware.AuthenticationMiddleware\n    'main.middleware.RedirectManagerMiddleware',",
    "'django.contrib.auth.middleware.AuthenticationMiddleware',\n    'main.middleware.RedirectManagerMiddleware',"
)

with open('tompuco/settings.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Fixed settings.py middleware')
