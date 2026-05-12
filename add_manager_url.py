import re

with open('tompuco/urls.py', 'r', encoding='utf-8') as f:
    content = f.read()

if "path('manager/'" not in content:
    # Add manager import at the top if not exists
    if "from manager import views" not in content and "from manager.urls" not in content:
        # Add after the last include
        content = content.replace(
            "path('committee/', include('committee.urls')),",
            "path('committee/', include('committee.urls')),\n    path('manager/', include('manager.urls')),"
        )
    else:
        content = content.replace(
            "urlpatterns = [",
            "urlpatterns = [\n    path('manager/', include('manager.urls')),"
        )
    
    with open('tompuco/urls.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added manager to main urls')
else:
    print('Manager URL already exists')
