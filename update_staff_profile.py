import re

with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Update StaffProfile model with role choices
new_staff_profile = '''
class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ('staff', 'Staff'),
        ('manager', 'Manager'),
        ('committee', 'Committee'),
        ('cashier', 'Cashier'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile')
    position = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    employee_id = models.CharField(max_length=50, blank=True)
    department = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='staff_profiles/%Y/%m/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    hire_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_position_display()}"
'''

# Find and replace the StaffProfile class
pattern = r'class StaffProfile\(models.Model\).*?(?=\nclass |\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_staff_profile, content, re.DOTALL)
    with open('main/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Updated StaffProfile model with role choices')
