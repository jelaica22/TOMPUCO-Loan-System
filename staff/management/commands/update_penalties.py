# staff/management/commands/update_penalties.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from main.models import Loan


class Command(BaseCommand):
    help = 'Update penalties for overdue loans'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        loans = Loan.objects.filter(status='active')

        updated_count = 0
        for loan in loans:
            old_penalty = loan.total_penalty_incurred
            new_penalty = loan.calculate_penalty(today)

            if new_penalty != old_penalty:
                loan.total_penalty_incurred = new_penalty
                loan.save(update_fields=['total_penalty_incurred'])
                updated_count += 1

                if new_penalty > 0:
                    self.stdout.write(f"Updated penalty for loan {loan.loan_number}: ₱{new_penalty:,.2f}")

        self.stdout.write(self.style.SUCCESS(f"Updated penalties for {updated_count} loans"))