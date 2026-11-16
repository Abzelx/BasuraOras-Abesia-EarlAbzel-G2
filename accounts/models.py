from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

phone_validator = RegexValidator(
    regex=r"^(\+63|0)9\d{9}$",
    message="Enter a valid Philippine mobile number, e.g. 09171234567 or +639171234567.",
)


class User(AbstractUser):
    """Custom user: Django's built-in user + a role + the SDD's extra fields."""

    class Role(models.TextChoices):
        RESIDENT = "RESIDENT", "Resident"
        STAFF = "STAFF", "Barangay Staff"

    email = models.EmailField("email address", blank=False)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.RESIDENT)
    phone_number = models.CharField(max_length=13, blank=True, validators=[phone_validator])

    # Resident-only fields
    street = models.ForeignKey(
        "locations.Street", null=True, blank=True, on_delete=models.PROTECT, related_name="residents"
    )
    house_details = models.CharField("house / landmark details", max_length=150, blank=True)

    # Staff-only fields
    barangay = models.ForeignKey(
        "locations.Barangay", null=True, blank=True, on_delete=models.PROTECT, related_name="staff_members"
    )
    position_title = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            # No two accounts may share an email, ignoring upper/lower case.
            models.UniqueConstraint(Lower("email"), name="uniq_user_email_ci",
                                    violation_error_message="An account with this email already exists."),
            # A resident must have a street and no barangay; staff the opposite.
            # Superusers (the admin you create with createsuperuser) are exempt.
            models.CheckConstraint(
                condition=(
                    Q(is_superuser=True)
                    | Q(role="RESIDENT", street__isnull=False, barangay__isnull=True)
                    | Q(role="STAFF", barangay__isnull=False, street__isnull=True)
                ),
                name="user_role_location_rules",
                violation_error_message="Residents need a street; staff need a barangay (not both).",
            ),
        ]

    @property
    def is_resident(self):
        return self.role == self.Role.RESIDENT

    @property
    def is_barangay_staff(self):
        return self.role == self.Role.STAFF

    @property
    def display_name(self):
        return self.get_full_name() or self.username
