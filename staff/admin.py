# staff/admin.py
from django.contrib import admin
from .models import StaffProfile, StaffActivityLog, StaffNotification, PaymentInstruction, RestructuringRequest

@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    list_display = ['staff_id', 'user', 'position', 'department', 'is_active']
    search_fields = ['staff_id', 'user__username', 'user__first_name', 'user__last_name']
    list_filter = ['position', 'department', 'is_active']

@admin.register(StaffActivityLog)
class StaffActivityLogAdmin(admin.ModelAdmin):
    list_display = ['staff', 'action', 'entity_type', 'created_at']
    list_filter = ['action', 'entity_type']
    search_fields = ['staff__user__username']

@admin.register(StaffNotification)
class StaffNotificationAdmin(admin.ModelAdmin):
    list_display = ['staff', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read']

@admin.register(PaymentInstruction)
class PaymentInstructionAdmin(admin.ModelAdmin):
    list_display = ['instruction_number', 'member_id', 'amount_to_collect', 'is_collected', 'issued_at']
    list_filter = ['is_collected', 'is_printed']

@admin.register(RestructuringRequest)
class RestructuringRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'member_id', 'old_balance', 'new_principal', 'status', 'created_at']
    list_filter = ['status']