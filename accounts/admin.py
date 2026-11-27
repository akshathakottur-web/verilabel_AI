
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class VerilabelUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('Verilabel', {'fields': ('name', 'role')}),)
    list_display = ('username', 'name', 'role', 'is_staff')


admin.site.register(User, VerilabelUserAdmin)
