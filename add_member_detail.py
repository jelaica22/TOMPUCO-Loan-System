import json

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if member_detail function exists and is correct
if 'def member_detail' not in content:
    member_detail_func = '''

@super_admin_required
def member_detail(request, member_id):
    """Get member details as JSON"""
    from django.http import JsonResponse
    from main.models import Member
    
    member = get_object_or_404(Member, id=member_id)
    return JsonResponse({
        'id': member.id,
        'membership_number': member.membership_number,
        'first_name': member.first_name,
        'last_name': member.last_name,
        'middle_initial': member.middle_initial,
        'nickname': getattr(member, 'nickname', ''),
        'nationality': getattr(member, 'nationality', 'Filipino'),
        'birthdate': member.birthdate.isoformat() if hasattr(member, 'birthdate') and member.birthdate else None,
        'gender': getattr(member, 'gender', ''),
        'age': getattr(member, 'age', ''),
        'contact_number': member.contact_number,
        'residence_address': member.residence_address,
        'spouse_name': getattr(member, 'spouse_name', ''),
        'num_dependents': getattr(member, 'num_dependents', 0),
        'farm_location': getattr(member, 'farm_location', ''),
        'farm_owned_hectares': str(getattr(member, 'farm_owned_hectares', 0)),
        'farm_leased_hectares': str(getattr(member, 'farm_leased_hectares', 0)),
        'adjacent_farm': getattr(member, 'adjacent_farm', ''),
        'area_planted': getattr(member, 'area_planted', ''),
        'new_plant': getattr(member, 'new_plant', ''),
        'ratoon_crops': getattr(member, 'ratoon_crops', ''),
        'other_loans': getattr(member, 'other_loans', ''),
        'employer_name': getattr(member, 'employer_name', ''),
        'position': getattr(member, 'position', ''),
        'years_with_employer': str(getattr(member, 'years_with_employer', 0)),
        'monthly_income': str(member.monthly_income),
        'is_active': member.is_active,
        'profile_picture': member.profile_picture.url if hasattr(member, 'profile_picture') and member.profile_picture else None,
        'created_at': member.created_at.isoformat() if member.created_at else None,
    })
'''
    content = content + member_detail_func
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added member_detail view')
else:
    print('member_detail view already exists')
