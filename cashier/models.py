# cashier/models.py
from django.db import models
from django.contrib.auth.models import User


class CashierProfile(models.Model):
    """Cashier profile"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cashier_profile')
    cashier_id = models.CharField(max_length=20, unique=True)
    position = models.CharField(max_length=50, default='cashier')
    branch = models.CharField(max_length=100, default='Main Branch')
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Cashier"