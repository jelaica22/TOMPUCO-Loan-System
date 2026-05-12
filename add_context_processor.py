import re

with open('tompuco/settings.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'main.context_processors.staff_profile_context' not in content:
    # Find TEMPLATES section
    pattern = r"'OPTIONS': \{[^}]*'context_processors': \[([^\]]*)\]"
    
    def add_processor(match):
        processors = match.group(1)
        if 'main.context_processors.staff_profile_context' not in processors:
            new_processors = processors.rstrip() + ",\n                'main.context_processors.staff_profile_context',"
            return match.group(0).replace(processors, new_processors)
        return match.group(0)
    
    content = re.sub(pattern, add_processor, content, flags=re.DOTALL)
    
    with open('tompuco/settings.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added staff_profile context processor')
