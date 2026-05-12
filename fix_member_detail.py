import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the member_detail function
old_member_detail = '''@super_admin_required
def member_detail(request, member_id):
    """View member details"""
    from django.http import JsonResponse
    member = get_object_or_404(Member, id=member_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "id": member.id,
            "membership_number": member.membership_number,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "middle_initial": member.middle_initial,
            "contact_number": member.contact_number,
            "residence_address": member.residence_address,
            "monthly_income": str(member.monthly_income),
            "is_active": member.is_active,
            "created_at": member.created_at.strftime("%Y-%m-%d") if member.created_at else None,
        })
    return render(request, "admin_panel/member_detail.html", {"member": member})'''

new_member_detail = '''@super_admin_required
def member_detail(request, member_id):
    """View member details - returns JSON for AJAX calls"""
    from django.http import JsonResponse
    member = get_object_or_404(Member, id=member_id)
    # Always return JSON for API calls
    return JsonResponse({
        "id": member.id,
        "membership_number": member.membership_number,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "middle_initial": member.middle_initial,
        "nickname": getattr(member, "nickname", ""),
        "nationality": getattr(member, "nationality", "Filipino"),
        "birthdate": member.birthdate.strftime("%Y-%m-%d") if hasattr(member, "birthdate") and member.birthdate else None,
        "gender": getattr(member, "gender", ""),
        "age": getattr(member, "age", ""),
        "contact_number": member.contact_number,
        "residence_address": member.residence_address,
        "spouse_name": getattr(member, "spouse_name", ""),
        "num_dependents": getattr(member, "num_dependents", 0),
        "farm_location": getattr(member, "farm_location", ""),
        "farm_owned_hectares": str(getattr(member, "farm_owned_hectares", 0)),
        "farm_leased_hectares": str(getattr(member, "farm_leased_hectares", 0)),
        "adjacent_farm": getattr(member, "adjacent_farm", ""),
        "area_planted": getattr(member, "area_planted", ""),
        "new_plant": getattr(member, "new_plant", ""),
        "ratoon_crops": getattr(member, "ratoon_crops", ""),
        "other_loans": getattr(member, "other_loans", ""),
        "employer_name": getattr(member, "employer_name", ""),
        "position": getattr(member, "position", ""),
        "years_with_employer": str(getattr(member, "years_with_employer", 0)),
        "monthly_income": str(member.monthly_income),
        "is_active": member.is_active,
        "profile_picture": member.profile_picture.url if hasattr(member, "profile_picture") and member.profile_picture else None,
        "created_at": member.created_at.strftime("%Y-%m-%d") if member.created_at else None,
    })'''

if 'def member_detail' in content:
    content = content.replace(old_member_detail, new_member_detail)
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Fixed member_detail view to always return JSON')
else:
    # If function doesn't exist, add it
    content = content + new_member_detail
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added member_detail view')
