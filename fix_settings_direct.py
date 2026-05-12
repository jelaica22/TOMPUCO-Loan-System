with open('tompuco/settings.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the middleware section
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'AuthenticationMiddleware' in line and ',' not in line and '],' not in line:
        # Fix the incomplete line
        new_lines.append("    'django.contrib.auth.middleware.AuthenticationMiddleware',\n")
        i += 1
        # Skip the next line if it contains the continuation
        if i < len(lines) and 'main.middleware' in lines[i]:
            new_lines.append("    'main.middleware.RedirectManagerMiddleware',\n")
            i += 1
    elif 'RedirectManagerMiddleware' in line and '],' not in line:
        # Already handled above
        i += 1
    else:
        new_lines.append(line)
        i += 1

with open('tompuco/settings.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✓ Fixed settings.py middleware section')
