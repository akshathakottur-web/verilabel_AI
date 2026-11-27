from django.contrib import admin

from .models import Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'name', 'check_type', 'field_key', 'weight', 'enabled')
    list_filter = ('enabled', 'check_type')
