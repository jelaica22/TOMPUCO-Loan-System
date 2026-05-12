with open('admin_panel/templates/admin_panel/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Update the user dropdown to include profile link
old_dropdown = '''<ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="#"><i class="bi bi-person-circle me-2"></i> My Profile</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" id="logoutBtnDropdown"><i class="bi bi-box-arrow-right me-2"></i> Logout</a></li>
                    </ul>'''

new_dropdown = '''<ul class="dropdown-menu dropdown-menu-end">
                        <li><a class="dropdown-item" href="{% url 'admin_panel:profile' %}"><i class="bi bi-person-circle me-2"></i> My Profile</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item text-danger" href="#" id="logoutBtnDropdown"><i class="bi bi-box-arrow-right me-2"></i> Logout</a></li>
                    </ul>'''

if old_dropdown in content:
    content = content.replace(old_dropdown, new_dropdown)
    with open('admin_panel/templates/admin_panel/base.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Updated user dropdown with profile link')
