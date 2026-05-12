with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Check if Payment model exists and update payment method choices
if 'class Payment' in content:
    # Replace payment method choices
    old_choices = "PAYMENT_METHOD_CHOICES = [\n        ('cash', 'Cash'),\n        ('bank_transfer', 'Bank Transfer'),\n        ('check', 'Check'),\n        ('paymaya', 'PayMaya'),\n    ]"
    new_choices = "PAYMENT_METHOD_CHOICES = [\n        ('cash', 'Cash'),\n        ('pesada', 'Pesada'),\n        ('quedan', 'Quedan'),\n    ]"
    
    if old_choices in content:
        content = content.replace(old_choices, new_choices)
        with open('main/models.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✓ Updated Payment model method choices to Cash, Pesada, Quedan')
    else:
        print('Old payment method choices not found, checking for other format...')
        
        # Try another pattern
        import re
        pattern = r"PAYMENT_METHOD_CHOICES = \[.*?\]"
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, "PAYMENT_METHOD_CHOICES = [\n        ('cash', 'Cash'),\n        ('pesada', 'Pesada'),\n        ('quedan', 'Quedan'),\n    ]", content, flags=re.DOTALL)
            with open('main/models.py', 'w', encoding='utf-8') as f:
                f.write(content)
            print('✓ Updated Payment model method choices using regex')
else:
    print('Payment class not found')
