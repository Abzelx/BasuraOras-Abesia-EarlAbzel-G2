from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.utils import timezone

from . import utils
from .models import CollectionSchedule, MissedReport

MAX_REPORTS_PER_DAY = 3  # BR-22
LOOKBACK_DAYS = 7  # BR-20


class MissedReportForm(forms.ModelForm):
    class Meta:
        model = MissedReport
        fields = ("schedule", "collection_date", "description")
        widgets = {
            "collection_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "description": forms.Textarea(attrs={"rows": 4, "maxlength": 500}),
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        today = utils.now_local().date()
        # A resident can only report on active schedule entries of their OWN street (BR-12, BR-20)
        self.fields["schedule"].queryset = CollectionSchedule.objects.filter(
            street_id=user.street_id, is_active=True
        ).select_related("street")
        self.fields["schedule"].empty_label = "-- choose the scheduled collection --"
        self.fields["schedule"].label = "Which scheduled collection was missed?"
        self.fields["collection_date"].widget.attrs.update(
            {"min": (today - timedelta(days=LOOKBACK_DAYS)).isoformat(), "max": today.isoformat()}
        )
        self.fields["description"].validators.append(MinLengthValidator(10, "Please describe what happened (at least 10 characters)."))

    def clean(self):
        cleaned = super().clean()
        schedule, date = cleaned.get("schedule"), cleaned.get("collection_date")
        now = utils.now_local()
        today = now.date()

        if schedule and date:
            if date > today:
                self.add_error("collection_date", "That collection hasn't happened yet.")
            elif date < today - timedelta(days=LOOKBACK_DAYS):
                self.add_error("collection_date", f"You can only report collections from the last {LOOKBACK_DAYS} days.")
            elif date.isoweekday() != schedule.day_of_week:
                self.add_error(
                    "collection_date",
                    f"{schedule.street.name} is collected on {schedule.get_day_of_week_display()}s, "
                    f"but {date:%b %d, %Y} is a {date:%A}.",
                )
            elif date == today and now.time() <= schedule.end_time:
                self.add_error(
                    "collection_date",
                    f"Today's collection window ends at {schedule.end_time:%I:%M %p}. Please report after that.",
                )
            elif MissedReport.objects.filter(user=self.user, schedule=schedule, collection_date=date).exists():
                raise ValidationError("You already reported this collection.")  # BR-21

        if not self.errors:
            recent = MissedReport.objects.filter(
                user=self.user, reported_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            if recent >= MAX_REPORTS_PER_DAY:
                raise ValidationError(f"You can submit at most {MAX_REPORTS_PER_DAY} reports within 24 hours.")  # BR-22
        return cleaned


class ReportEditForm(forms.ModelForm):
    """After submitting, a resident may only reword the description (and only while SUBMITTED)."""

    class Meta:
        model = MissedReport
        fields = ("description",)
        widgets = {"description": forms.Textarea(attrs={"rows": 4, "maxlength": 500})}
