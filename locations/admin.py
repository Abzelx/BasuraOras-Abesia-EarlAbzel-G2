from django.contrib import admin

from .models import Barangay, Street


@admin.register(Barangay)
class BarangayAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    list_display = ("name", "purok", "barangay")
    list_filter = ("barangay",)
    search_fields = ("name", "purok")
