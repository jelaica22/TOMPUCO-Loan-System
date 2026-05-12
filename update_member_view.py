import re

with open('admin_panel/templates/admin_panel/members_list.html', 'r', encoding='utf-8') as f:
    content = f.read()

# New viewMember function
new_view_function = '''function viewMember(memberId) {
    fetch(`/superadmin/members/${memberId}/`)
        .then(response => response.json())
        .then(data => {
            let birthdate = data.birthdate ? new Date(data.birthdate).toLocaleDateString() : '-';
            let profileHtml = '';
            if (data.profile_picture) {
                profileHtml = '<img src="' + data.profile_picture + '" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #1e3c72;">';
            } else {
                let initials = (data.first_name ? data.first_name.charAt(0) : '') + (data.last_name ? data.last_name.charAt(0) : '');
                profileHtml = '<div style="width: 100px; height: 100px; border-radius: 50%; background: #1e3c72; display: inline-flex; align-items: center; justify-content: center; color: white; font-size: 2rem;">' + initials + '</div>';
            }
            let html = `
                <div class="row">
                    <div class="col-12 text-center mb-3">
                        ${profileHtml}
                    </div>
                </div>
                <div class="row">
                    <div class="col-5"><strong>Member #:</strong></div><div class="col-7">${data.membership_number || '-'}</div>
                    <div class="col-5 mt-2"><strong>Full Name:</strong></div><div class="col-7 mt-2">${data.first_name} ${data.last_name} ${data.middle_initial ? data.middle_initial + '.' : ''}</div>
                    <div class="col-5 mt-2"><strong>Nickname:</strong></div><div class="col-7 mt-2">${data.nickname || '-'}</div>
                    <div class="col-5 mt-2"><strong>Nationality:</strong></div><div class="col-7 mt-2">${data.nationality || 'Filipino'}</div>
                    <div class="col-5 mt-2"><strong>Birthdate:</strong></div><div class="col-7 mt-2">${birthdate}</div>
                    <div class="col-5 mt-2"><strong>Gender:</strong></div><div class="col-7 mt-2">${data.gender || '-'}</div>
                    <div class="col-5 mt-2"><strong>Age:</strong></div><div class="col-7 mt-2">${data.age || '-'}</div>
                    <div class="col-5 mt-2"><strong>Contact #:</strong></div><div class="col-7 mt-2">${data.contact_number || '-'}</div>
                    <div class="col-5 mt-2"><strong>Residence Address:</strong></div><div class="col-7 mt-2">${data.residence_address || '-'}</div>
                    <div class="col-5 mt-2"><strong>Spouse:</strong></div><div class="col-7 mt-2">${data.spouse_name || 'N/A'}</div>
                    <div class="col-5 mt-2"><strong>Dependents:</strong></div><div class="col-7 mt-2">${data.num_dependents || 0}</div>
                    <div class="col-5 mt-2"><strong>Farm Location:</strong></div><div class="col-7 mt-2">${data.farm_location || '-'}</div>
                    <div class="col-5 mt-2"><strong>Owned:</strong></div><div class="col-7 mt-2">${data.farm_owned_hectares || 0} has.</div>
                    <div class="col-5 mt-2"><strong>Leased:</strong></div><div class="col-7 mt-2">${data.farm_leased_hectares || 0} has.</div>
                    <div class="col-5 mt-2"><strong>Adjacent Farm:</strong></div><div class="col-7 mt-2">${data.adjacent_farm || '-'}</div>
                    <div class="col-5 mt-2"><strong>Area Planted:</strong></div><div class="col-7 mt-2">${data.area_planted || '-'}</div>
                    <div class="col-5 mt-2"><strong>New Plant:</strong></div><div class="col-7 mt-2">${data.new_plant || '-'}</div>
                    <div class="col-5 mt-2"><strong>Ratoon Crops:</strong></div><div class="col-7 mt-2">${data.ratoon_crops || '-'}</div>
                    <div class="col-5 mt-2"><strong>Other Loans:</strong></div><div class="col-7 mt-2">${data.other_loans || 'None'}</div>
                    <div class="col-5 mt-2"><strong>Employer:</strong></div><div class="col-7 mt-2">${data.employer_name || '-'}</div>
                    <div class="col-5 mt-2"><strong>Position:</strong></div><div class="col-7 mt-2">${data.position || '-'}</div>
                    <div class="col-5 mt-2"><strong>Years with Employer:</strong></div><div class="col-7 mt-2">${data.years_with_employer || 0}</div>
                    <div class="col-5 mt-2"><strong>Monthly Income:</strong></div><div class="col-7 mt-2">₱${parseFloat(data.monthly_income || 0).toLocaleString()}</div>
                    <div class="col-5 mt-2"><strong>Status:</strong></div><div class="col-7 mt-2">${data.is_active ? '<span class="badge-active">Active</span>' : '<span class="badge-inactive">Inactive</span>'}</div>
                    <div class="col-5 mt-2"><strong>Member Since:</strong></div><div class="col-7 mt-2">${data.created_at || '-'}</div>
                </div>
            `;
            document.getElementById('viewMemberContent').innerHTML = html;
            new bootstrap.Modal(document.getElementById('viewMemberModal')).show();
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('viewMemberContent').innerHTML = '<div class="alert alert-danger">Error loading member details. Please try again.</div>';
            new bootstrap.Modal(document.getElementById('viewMemberModal')).show();
        });
}'''

# Find the old viewMember function and replace it
pattern = r'function viewMember\(memberId\).*?\n\}'
content = re.sub(pattern, new_view_function, content, flags=re.DOTALL)

with open('admin_panel/templates/admin_panel/members_list.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('✓ Updated viewMember function with complete member details')
