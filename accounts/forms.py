from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from locations.models import Street

User = get_user_model()


def _email_taken(email, exclude_pk=None):
    qs = User.objects.filter(email__iexact=email)
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


class RegistrationForm(UserCreationForm):
    """Resident self-registration. (Staff accounts are created by an admin.)"""

    street = forms.ModelChoiceField(
        queryset=Street.objects.none(),
        label="Your street / purok",
        empty_label="-- choose your street --",
        error_messages={"required": "Please choose your street."},
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone_number", "street")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # BR-05: only streets that belong to active barangays can be chosen.
        self.fields["street"].queryset = Street.objects.filter(barangay__is_active=True).select_related("barangay")
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True
        self.instance.role = User.Role.RESIDENT

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if _email_taken(email):
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)  # password is hashed here by set_password()
        user.role = User.Role.RESIDENT
        if commit:
            user.save()
        return user


class ProfileForm(forms.ModelForm):
    """Edit your own details. Residents may change street; staff may change position title."""

    street = forms.ModelChoiceField(queryset=Street.objects.none(), label="Your street / purok")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone_number", "street", "house_details", "position_title")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("first_name", "last_name", "email"):
            self.fields[name].required = True
        if self.instance.role == User.Role.RESIDENT:
            self.fields["street"].queryset = Street.objects.filter(barangay__is_active=True).select_related("barangay")
            del self.fields["position_title"]
        else:
            del self.fields["street"]
            del self.fields["house_details"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if _email_taken(email, exclude_pk=self.instance.pk):
            raise forms.ValidationError("An account with this email already exists.")
        return email
