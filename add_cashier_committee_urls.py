# Update main urls.py to include cashier and committee
import re

with open('tompuco/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('cashier/'" not in content:
    content = content.replace(
        "urlpatterns = [",
        "urlpatterns = [\n    path('cashier/', include('cashier.urls')),\n    path('committee/', include('committee.urls')),"
    )
    with open('tompuco/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added cashier and committee to main urls')
