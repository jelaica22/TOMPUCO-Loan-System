with open('tompuco/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'main.middleware.RedirectManagerMiddleware' not in content:
    # Add middleware after AuthenticationMiddleware
    content = content.replace(
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware\n    \'main.middleware.RedirectManagerMiddleware\','
    )
    with open('tompuco/settings.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added RedirectManagerMiddleware to settings')
