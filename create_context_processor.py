# Create context_processors.py
import os

context_processor = '''
from main.models import StaffProfile

def staff_profile_context(request):
    """Add staff_profile to all templates"""
    if request.user.is_authenticated:
        profile, created = StaffProfile.objects.get_or_create(user=request.user)
        return {'staff_profile': profile}
    return {}
'''

with open('main/context_processors.py', 'w', encoding='utf-8') as f:
    f.write(context_processor)
print('✓ Created context processor for staff profile')
