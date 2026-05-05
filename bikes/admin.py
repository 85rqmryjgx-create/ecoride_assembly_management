from django.contrib import admin
from .models import BikeModel, Component


class ComponentInline(admin.TabularInline):
    model = Component
    extra = 1


@admin.register(BikeModel)
class BikeModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'year', 'active']
    list_filter = ['brand', 'active']
    inlines = [ComponentInline]
