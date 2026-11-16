from datetime import time

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from locations.models import Street
from pickups.models import CollectionSchedule

# street name -> list of weekdays (1=Mon ... 7=Sun)
PLAN = {
    "Rizal Street": [1, 4],
    "Mabini Street": [2, 5],
    "Bonifacio Street": [1, 4],
    "Luna Street": [3, 6],
    "Sampaguita Lane": [2, 5],
}


class Command(BaseCommand):
    help = "Create sample collection schedules for the sample streets. Needs at least one staff user."

    def handle(self, *args, **options):
        staff = User.objects.filter(role=User.Role.STAFF).first()
        if staff is None:
            raise CommandError("Create a staff user first (in /admin/, set role = Staff and a barangay).")
        created = 0
        for street_name, days in PLAN.items():
            for street in Street.objects.filter(name=street_name):
                for day in days:
                    _, was_created = CollectionSchedule.objects.get_or_create(
                        street=street, day_of_week=day,
                        defaults={"start_time": time(7, 0), "end_time": time(10, 0), "created_by": staff},
                    )
                    created += was_created
        self.stdout.write(self.style.SUCCESS(f"Done. {created} new schedule entries."))
