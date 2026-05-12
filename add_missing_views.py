import re

with open('admin_panel/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_functions = '''

@super_admin_required
def user_detail(request, user_id):
    """View user details"""
    from django.http import JsonResponse
    user = get_object_or_404(User, id=user_id)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "is_active": user.is_active,
            "last_login": user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else None,
            "date_joined": user.date_joined.strftime("%Y-%m-%d %H:%M"),
        })
    return render(request, "admin_panel/user_detail.html", {"user": user})


@super_admin_required
def user_edit(request, user_id):
    """Edit user"""
    user = get_object_or_404(User, id=user_id)
    if request.method == "POST":
        user.username = request.POST.get("username")
        user.email = request.POST.get("email")
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.is_staff = request.POST.get("is_staff") == "on"
        user.is_superuser = request.POST.get("is_superuser") == "on"
        user.is_active = request.POST.get("is_active") == "on"
        
        password = request.POST.get("password")
        if password:
            user.set_password(password)
        
        user.save()
        messages.success(request, f"User {user.username} updated successfully")
        return redirect("admin_panel:users_list")
    
    return render(request, "admin_panel/user_form.html", {"user": user, "action": "Edit"})


@super_admin_required
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
    return render(request, "admin_panel/member_detail.html", {"member": member})
'''

# Check if functions exist
if 'def user_detail' not in content:
    content = content + new_functions
    with open('admin_panel/views.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added user_detail, user_edit, and member_detail functions')
else:
    print('✓ Functions already exist')
