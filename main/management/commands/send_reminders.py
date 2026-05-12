from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import Loan, PaymentReminder, Notification
from decimal import Decimal

class Command(BaseCommand):
    help = 'Send payment reminders to members with upcoming due dates'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Check for upcoming due dates
        reminders_sent = 0
        
        # 7 days before due
        seven_days = today + timedelta(days=7)
        loans_7days = Loan.objects.filter(
            due_date=seven_days, 
            status='active',
            remaining_balance__gt=0
        )
        
        for loan in loans_7days:
            if not PaymentReminder.objects.filter(
                loan=loan, 
                reminder_type='7_days',
                sent_at__date=today
            ).exists():
                # Create notification for member
                Notification.objects.create(
                    user=loan.borrower.user,
                    title='Payment Reminder - 7 Days',
                    message=f'Your payment of ₱{loan.monthly_payment:,.2f} for loan {loan.loan_number} is due in 7 days.',
                    notification_type='payment_reminder',
                    link=f'/my-loans/{loan.id}/'
                )
                PaymentReminder.objects.create(
                    loan=loan,
                    reminder_type='7_days'
                )
                reminders_sent += 1
        
        # 3 days before due
        three_days = today + timedelta(days=3)
        loans_3days = Loan.objects.filter(
            due_date=three_days, 
            status='active',
            remaining_balance__gt=0
        )
        
        for loan in loans_3days:
            if not PaymentReminder.objects.filter(
                loan=loan, 
                reminder_type='3_days',
                sent_at__date=today
            ).exists():
                Notification.objects.create(
                    user=loan.borrower.user,
                    title='Payment Reminder - 3 Days',
                    message=f'Urgent: Your payment of ₱{loan.monthly_payment:,.2f} for loan {loan.loan_number} is due in 3 days.',
                    notification_type='payment_reminder',
                    link=f'/my-loans/{loan.id}/'
                )
                PaymentReminder.objects.create(
                    loan=loan,
                    reminder_type='3_days'
                )
                reminders_sent += 1
        
        # 1 day before due
        one_day = today + timedelta(days=1)
        loans_1day = Loan.objects.filter(
            due_date=one_day, 
            status='active',
            remaining_balance__gt=0
        )
        
        for loan in loans_1day:
            if not PaymentReminder.objects.filter(
                loan=loan, 
                reminder_type='1_day',
                sent_at__date=today
            ).exists():
                Notification.objects.create(
                    user=loan.borrower.user,
                    title='Payment Due Tomorrow!',
                    message=f'Your payment of ₱{loan.monthly_payment:,.2f} for loan {loan.loan_number} is due TOMORROW.',
                    notification_type='payment_reminder',
                    link=f'/my-loans/{loan.id}/'
                )
                PaymentReminder.objects.create(
                    loan=loan,
                    reminder_type='1_day'
                )
                reminders_sent += 1
        
        # Overdue tracking
        overdue_loans = Loan.objects.filter(
            due_date__lt=today,
            status='active',
            remaining_balance__gt=0
        )
        
        for loan in overdue_loans:
            days_overdue = (today - loan.due_date).days
            
            if days_overdue == 7:
                Notification.objects.create(
                    user=loan.borrower.user,
                    title='⚠️ Payment Overdue - 7 Days',
                    message=f'Your payment for loan {loan.loan_number} is 7 days overdue. Please pay immediately to avoid penalties.',
                    notification_type='overdue_reminder',
                    link=f'/my-loans/{loan.id}/'
                )
                PaymentReminder.objects.create(
                    loan=loan,
                    reminder_type='overdue_7'
                )
                reminders_sent += 1
            elif days_overdue == 15:
                # Calculate penalty
                penalty = loan.remaining_balance * Decimal('0.02')
                Notification.objects.create(
                    user=loan.borrower.user,
                    title='⚠️ URGENT - 15 Days Overdue',
                    message=f'Your loan {loan.loan_number} is 15 days overdue. Penalty of ₱{penalty:,.2f} has been applied.',
                    notification_type='overdue_reminder',
                    link=f'/my-loans/{loan.id}/'
                )
                PaymentReminder.objects.create(
                    loan=loan,
                    reminder_type='overdue_15'
                )
                reminders_sent += 1
            elif days_overdue == 30:
                Notification.objects.create(
                    user=loan.borrower.user,
                    title='⚠️ FINAL NOTICE - 30 Days Overdue',
                    message=f'Your loan {loan.loan_number} is 30 days overdue. Please contact the cooperative immediately.',
                    notification_type='overdue_reminder',
                    link=f'/my-loans/{loan.id}/'
                )
                PaymentReminder.objects.create(
                    loan=loan,
                    reminder_type='overdue_30'
                )
                reminders_sent += 1
        
        # Also notify staff about overdue accounts
        if overdue_loans.exists():
            staff_users = User.objects.filter(is_staff=True)
            for staff in staff_users:
                Notification.objects.create(
                    user=staff,
                    title='Overdue Accounts Alert',
                    message=f'There are {overdue_loans.count()} overdue loan accounts requiring attention.',
                    notification_type='staff_alert',
                    link='/staff/loans/'
                )
        
        self.stdout.write(self.style.SUCCESS(f'Sent {reminders_sent} payment reminders'))
