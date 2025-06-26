from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

#modelo do user que expande do modelo original do Django
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_email_verified')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_email_verified')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'address', 'city', 'state', 'zipcode', 'country', 'is_email_verified')
        }),
    )