from django.db import models
from django.conf import settings


class CommitteeProfile(models.Model):
    POSITION_CHOICES = [
        ('member', 'Committee Member'),
        ('head', 'Head Committee'),
        ('secretary', 'Secretary'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='committee_profile')
    avatar = models.ImageField(upload_to='committee_avatars/', null=True, blank=True)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default='member')
    committee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True)
    is_head = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.committee_id:
            self.committee_id = f"COM{self.user.id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_position_display()}"