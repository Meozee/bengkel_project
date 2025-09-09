# core/admin.py

from django.contrib import admin
from .models import ActivityLog

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action_type', 'action_details', 'timestamp', 'is_read')
    list_filter = ('action_type', 'timestamp', 'actor')
    # Log seharusnya tidak bisa diubah dari admin
    readonly_fields = ('actor', 'action_type', 'action_details', 'timestamp', 'content_object')