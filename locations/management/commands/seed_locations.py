from django.core.management.base import BaseCommand

from locations.models import Barangay, Street

SAMPLE = {
    "Sample Barangay (rename me in /admin)": [
        ("Rizal Street", "Purok 1"),
        ("Mabini Street", "Purok 1"),
        ("Bonifacio Street", "Purok 2"),
        ("Luna Street", "Purok 2"),
        ("Sampaguita Lane", "Purok 3"),
    ]
}


class Command(BaseCommand):
    help = "Create sample barangay/street data so you can test registration. Safe to run many times."

    def handle(self, *args, **options):
        for barangay_name, streets in SAMPLE.items():
            barangay, _ = Barangay.objects.get_or_create(name=barangay_name)
            for street_name, purok in streets:
                Street.objects.get_or_create(barangay=barangay, name=street_name, purok=purok)
        self.stdout.write(self.style.SUCCESS("Sample locations ready."))
