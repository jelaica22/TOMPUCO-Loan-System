# manager/management/commands/generate_manager_notifications.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from main.models import Notification
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Generate sample notifications for managers'

    def handle(self, *args, **options):
        managers = User.objects.filter(manager_profile__isnull=True)
        
        if managers.exists():
            self.stdout.write(self.style.ERROR(f'Found {managers.count()} managers'))
        else:
            self.stdout.write(self.style.ERROR('No managers found!'))
            return
        
        notification_types = [
            ('application', 'New Application', 'A new loan application from {member} is ready for review.'),
            ('committee', 'Committee Decision', 'Committee decision ready for application #{app_id}.'),
            ('system', 'System Update', 'The system has been updated with new features.'),
            ('reminder', 'Reminder', 'You have {count} pending applications waiting.'),
        ]
        
        member_names = ['Juan Dela Cruz', 'Maria Santos', 'Pedro Reyes', 'Ana Garcia', 'Jose Mendoza']
        created_count = 0
        
        for manager in managers:
            for i in range(8):
                notif_type, title, msg = random.choice(notification_types)
                member = random.choice(member_names)
                app_id = f"APP-{random.randint(1000, 9999)}"
                count = random.randint(1, 5)
                
                message = msg.format(member=member, app_id=app_id, count=count)
                days_ago = random.randint(0, 5)
                created_at = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
                is_read = random.choice([True, False, False])
                
                Notification.objects.create(
                    recipient=manager,
                    notification_type=notif_type,
                    title=f"{title} - {member}",
                    message=message,
                    link='/manager/pending-approvals/',
                    is_read=is_read,
                    created_at=created_at
                )
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✅ Created {created_count} sample notifications!'))
