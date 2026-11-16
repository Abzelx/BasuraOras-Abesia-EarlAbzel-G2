from django.contrib import admin

from .models import CollectionSchedule, MissedReport


@admin.register(CollectionSchedule)
class CollectionScheduleAdmin(admin.ModelAdmin):
    list_display = ("street", "day_of_week", "start_time", "end_time", "is_active")
    list_filter = ("is_active", "day_of_week", "street__barangay")


@admin.register(MissedReport)
class MissedReportAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "schedule", "collection_date", "status", "reported_at")
    list_filter = ("status",)
    search_fields = ("user__username", "description")
