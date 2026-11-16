from django import forms

from locations.models import Street

from .models import CollectionSchedule

_time = forms.TimeInput(attrs={"type": "time"}, format="%H:%M")


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = CollectionSchedule
        fields = ("street", "day_of_week", "start_time", "end_time", "is_active")
        widgets = {"start_time": _time, "end_time": _time}

    def __init__(self, *args, staff_user, **kwargs):
        super().__init__(*args, **kwargs)
        # BR-10: staff may only manage streets in their own barangay
        self.fields["street"].queryset = Street.objects.filter(barangay=staff_user.barangay)

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get("start_time"), cleaned.get("end_time")
        if start and end and end <= start:
            self.add_error("end_time", "End time must be later than the start time.")
        return cleaned
