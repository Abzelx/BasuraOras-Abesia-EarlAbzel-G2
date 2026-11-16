from django.conf import settings
from django.db import models
from django.db.models import F, Q


class CollectionSchedule(models.Model):
    """One collection slot for one street on one weekday (SDD table: collection_schedule)."""

    class Day(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    street = models.ForeignKey("locations.Street", on_delete=models.PROTECT, related_name="schedules")
    day_of_week = models.PositiveSmallIntegerField(choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True, help_text="Inactive entries are hidden from residents.")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="schedules_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["street__name", "day_of_week", "start_time"]
        constraints = [
            # BR-08: one entry per street per weekday
            models.UniqueConstraint(
                fields=["street", "day_of_week"], name="uniq_schedule_street_day",
                violation_error_message="This street already has a schedule entry for that day.",
            ),
            # BR-09
            models.CheckConstraint(condition=Q(day_of_week__gte=1, day_of_week__lte=7), name="schedule_day_1_to_7"),
            models.CheckConstraint(condition=Q(end_time__gt=F("start_time")), name="schedule_end_after_start"),
        ]

    def __str__(self):
        return (f"{self.street.name} – {self.get_day_of_week_display()} "
                f"{self.start_time:%I:%M %p}–{self.end_time:%I:%M %p}")
