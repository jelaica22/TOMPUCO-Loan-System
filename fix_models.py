import re

with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace 'User' with 'auth.User' for ForeignKey references
content = content.replace("models.ForeignKey('User'", "models.ForeignKey('auth.User'")
content = content.replace("models.ForeignKey(User,", "models.ForeignKey('auth.User',")

with open('main/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed model references to use 'auth.User'")
