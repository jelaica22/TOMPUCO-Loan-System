from django.core.management.base import BaseCommand
from main.models import Role


class Command(BaseCommand):
    help = 'Create the 6 default roles for the system'

    def handle(self, *args, **kwargs):
        roles = [
            {
                'name': 'member',
                'description': 'Member (Borrower) - Can apply for loans, view own applications',
                'can_apply_loan': True,
            },
            {
                'name': 'staff',
                'description': 'Staff (Loan Officer) - Can review applications, add charges',
                'can_review_applications': True,
                'can_add_charges': True,
            },
            {
                'name': 'committee',
                'description': 'Committee Member - Can approve loan line amount',
                'can_approve_line': True,
            },
            {
                'name': 'manager',
                'description': 'Manager - Can final approve loans, generate reports',
                'can_final_approve': True,
                'can_generate_reports': True,
            },
            {
                'name': 'cashier',
                'description': 'Cashier - Can post payments only',
                'can_post_payments': True,
            },
            {
                'name': 'super_admin',
                'description': 'Super Admin - Full system access',
                'can_manage_users': True,
                'can_generate_reports': True,
                'can_final_approve': True,
            },
        ]

        for role_data in roles:
            role, created = Role.objects.update_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created role: {role.get_name_display()}'))
            else:
                self.stdout.write(self.style.WARNING(f'Role already exists: {role.get_name_display()}'))

        self.stdout.write(self.style.SUCCESS('\n✅ All 6 roles created successfully!'))