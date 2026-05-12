import re

with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'profile_picture' not in content:
    # Find the Member class and add profile_picture field
    pattern = r'(class Member\(models.Model\):.*?)(\n    def __str__)'
    replacement = r'\1    profile_picture = models.ImageField(upload_to="member_profiles/%Y/%m/", null=True, blank=True)\n    \2'
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    with open('main/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added profile_picture field to Member model')
else:
    print('Profile picture field already exists')
