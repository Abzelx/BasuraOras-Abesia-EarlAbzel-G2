from django.conf import settings
from django.db import models
from django.db.models import Q


class MissedReport(models.Model):
    """A resident's report that a scheduled pickup did not happen (SDD table: missed_report)."""

    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged"
        RESOLVED = "RESOLVED", "Resolved"
        DISMISSED = "DISMISSED", "Dismissed"

    # BR-23: allowed status changes. RESOLVED and DISMISSED are final.
    NEXT_STATUSES = {
        "SUBMITTED": ["ACKNOWLEDGED", "DISMISSED"],
        "ACKNOWLEDGED": ["RESOLVED", "DISMISSED"],
    }
    FINAL_STATUSES = ["RESOLVED", "DISMISSED"]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="missed_reports")
    schedule = models.ForeignKey("pickups.CollectionSchedule", on_delete=models.PROTECT, related_name="missed_reports")
    collection_date = models.DateField(help_text="The date the pickup was supposed to happen.")
    description = models.TextField(max_length=500, help_text="What happened? (max 500 characters)")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    staff_response = models.TextField(max_length=500, blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="handled_reports"
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-reported_at"]
        constraints = [
            # BR-21
            models.UniqueConstraint(
                fields=["user", "schedule", "collection_date"], name="uniq_report_user_schedule_date",
                violation_error_message="You already reported this collection.",
            ),
            # BR-24: a finished report records who handled it and when
            models.CheckConstraint(
                condition=~Q(status__in=["RESOLVED", "DISMISSED"]) | Q(handled_by__isnull=False, resolved_at__isnull=False),
                name="report_final_needs_handler",
            ),
            # BR-24: a dismissed report must explain why
            models.CheckConstraint(
                condition=~Q(status="DISMISSED") | ~Q(staff_response=""),
                name="report_dismissed_needs_response",
            ),
        ]

    def __str__(self):
        return f"Report #{self.pk} – {self.schedule.street.name} on {self.collection_date}"

    @property
    def is_final(self):
        return self.status in self.FINAL_STATUSES

    @property
    def can_resident_edit(self):
        return self.status == self.Status.SUBMITTED

    @property
    def allowed_next_statuses(self):
        return self.NEXT_STATUSES.get(self.status, [])
