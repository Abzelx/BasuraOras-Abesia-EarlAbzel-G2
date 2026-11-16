from django.db import models


class Barangay(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(
        default=True, help_text="Only active barangays accept new resident registrations (BR-05)."
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "barangays"

    def __str__(self):
        return self.name


class Street(models.Model):
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE, related_name="streets")
    name = models.CharField(max_length=120, help_text="Street name")
    purok = models.CharField(max_length=60, blank=True, help_text="Purok / zone, e.g. 'Purok 3'")

    class Meta:
        ordering = ["barangay__name", "purok", "name"]
        constraints = [
            models.UniqueConstraint(fields=["barangay", "name", "purok"], name="uniq_street_per_barangay_purok"),
        ]

    def __str__(self):
        label = f"{self.name}, {self.purok}" if self.purok else self.name
        return f"{label} ({self.barangay.name})"
