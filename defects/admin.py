from django.contrib import admin
from .models import Defect


@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ['pk', 'defect_type', 'severity', 'session', 'reported_by', 'reported_at', 'is_resolved']
    list_filter = ['defect_type', 'severity', 'resolved_at']
    readonly_fields = ['reported_at', 'resolved_at']
