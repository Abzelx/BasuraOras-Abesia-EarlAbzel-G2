from django import forms

from .models import MissedReport


class StaffReviewForm(forms.Form):
    status = forms.ChoiceField(label="Change status to")
    staff_response = forms.CharField(
        label="Response to the resident", required=False, max_length=500,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
    )

    def __init__(self, *args, report, **kwargs):
        super().__init__(*args, **kwargs)
        # BR-23: only offer the status changes that are allowed from the current status
        self.fields["status"].choices = [
            (value, MissedReport.Status(value).label) for value in report.allowed_next_statuses
        ]
        self.fields["staff_response"].initial = report.staff_response

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("status") == MissedReport.Status.DISMISSED and not (cleaned.get("staff_response") or "").strip():
            self.add_error("staff_response", "Please explain why you are dismissing this report.")  # BR-24
        return cleaned
