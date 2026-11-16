from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class BasuraUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "street", "barangay", "is_active")
    list_filter = ("role", "is_active", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")

    fieldsets = UserAdmin.fieldsets + (
        ("BasuraOras", {"fields": ("role", "phone_number", "street", "house_details", "barangay", "position_title")}),
    )
    # Staff accounts are created here (admins only), not through public registration.
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("BasuraOras", {"fields": ("email", "role", "street", "barangay", "position_title")}),
    )
