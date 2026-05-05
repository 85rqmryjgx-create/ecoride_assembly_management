from django.contrib import admin
from .models import AssemblyProcess, AssemblyStep, AssemblySession, StepExecution


class StepInline(admin.TabularInline):
    model = AssemblyStep
    extra = 1


@admin.register(AssemblyProcess)
class ProcessAdmin(admin.ModelAdmin):
    list_display = ['name', 'bike_model', 'active', 'created_by']
    list_filter = ['bike_model', 'active']
    inlines = [StepInline]


class StepExecutionInline(admin.TabularInline):
    model = StepExecution
    extra = 0


@admin.register(AssemblySession)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['pk', 'bike_model', 'process', 'worker', 'status', 'started_at']
    list_filter = ['status', 'bike_model']
    inlines = [StepExecutionInline]
