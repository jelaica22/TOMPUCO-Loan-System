from django.db import models
from django.contrib.auth.models import User


class ManagerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='manager_profile')
    profile_picture = models.ImageField(upload_to='manager_profiles/', null=True, blank=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)

    # Two-Factor Authentication
    otp_enabled = models.BooleanField(default=False)
    otp_secret = models.CharField(max_length=100, blank=True, null=True)
    otp_backup_codes = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Manager Profile"