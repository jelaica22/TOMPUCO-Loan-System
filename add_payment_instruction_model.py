import re

with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'class PaymentInstruction' not in content:
    payment_instruction_model = '''

# Payment Instruction Model
class PaymentInstruction(models.Model):
    instruction_number = models.CharField(max_length=50, unique=True)
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='payment_instructions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], default='pending')
    issued_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='issued_instructions')
    issued_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.instruction_number} - {self.loan.loan_number} - ₱{self.amount:,.2f}"
'''
    content = content + payment_instruction_model
    with open('main/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added PaymentInstruction model')
else:
    print('PaymentInstruction model already exists')
