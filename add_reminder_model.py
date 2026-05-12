# Add to main/models.py - Payment Reminder tracking
import sys
sys.path.insert(0, '.')

with open('main/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'class PaymentReminder' not in content:
    reminder_model = '''

# Payment Reminder Tracking
class PaymentReminder(models.Model):
    REMINDER_TYPES = [
        ('7_days', '7 Days Before Due'),
        ('3_days', '3 Days Before Due'),
        ('1_day', '1 Day Before Due'),
        ('due_date', 'Due Date'),
        ('overdue_7', '7 Days Overdue'),
        ('overdue_15', '15 Days Overdue'),
        ('overdue_30', '30 Days Overdue'),
    ]
    loan = models.ForeignKey('Loan', on_delete=models.CASCADE, related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Reminder for {self.loan.loan_number} - {self.get_reminder_type_display()}"
'''
    content = content + reminder_model
    with open('main/models.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Added PaymentReminder model')
