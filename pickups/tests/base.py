from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from locations.models import Barangay, Street
from pickups.models import CollectionSchedule, MissedReport

PASSWORD = "Garbage2026x"
FAKE_TODAY = date(2026, 11, 16)  # a Monday (isoweekday 1)
YESTERDAY = FAKE_TODAY - timedelta(days=1)  # Sunday (7)


class PickupTestCase(TestCase):
    """Shared data. 'Today' is frozen to Mon 16 Nov 2026, 3:00 PM so date rules are predictable."""

    @classmethod
    def setUpTestData(cls):
        cls.brgy = Barangay.objects.create(name="Barangay A")
        cls.brgy_b = Barangay.objects.create(name="Barangay B")
        cls.street = Street.objects.create(barangay=cls.brgy, name="Rizal St", purok="Purok 1")
        cls.street2 = Street.objects.create(barangay=cls.brgy, name="Mabini St", purok="Purok 2")
        cls.street_b = Street.objects.create(barangay=cls.brgy_b, name="Luna St")

        def make(username, role, **kw):
            return User.objects.create_user(
                username=username, email=f"{username}@example.com", password=PASSWORD,
                first_name=username.title(), last_name="Tester", role=role, **kw)

        cls.juan = make("juan", User.Role.RESIDENT, street=cls.street)
        cls.maria = make("maria", User.Role.RESIDENT, street=cls.street2)
        cls.staff = make("staffa", User.Role.STAFF, barangay=cls.brgy)
        cls.staff_b = make("staffb", User.Role.STAFF, barangay=cls.brgy_b)

        # Rizal St: Sunday and Monday 7-10 AM. Mabini St: Sunday.
        cls.sunday = CollectionSchedule.objects.create(
            street=cls.street, day_of_week=7, start_time=time(7), end_time=time(10), created_by=cls.staff)
        cls.monday = CollectionSchedule.objects.create(
            street=cls.street, day_of_week=1, start_time=time(7), end_time=time(10), created_by=cls.staff)
        cls.mabini_sunday = CollectionSchedule.objects.create(
            street=cls.street2, day_of_week=7, start_time=time(7), end_time=time(10), created_by=cls.staff)
        cls.sched_b = CollectionSchedule.objects.create(
            street=cls.street_b, day_of_week=7, start_time=time(7), end_time=time(10), created_by=cls.staff_b)

    def setUp(self):
        fake_now = timezone.make_aware(datetime.combine(FAKE_TODAY, time(15, 0)))
        patcher = patch("pickups.utils.now_local", return_value=fake_now)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_report(self, user=None, schedule=None, when=YESTERDAY, **kw):
        return MissedReport.objects.create(
            user=user or self.juan, schedule=schedule or self.sunday, collection_date=when,
            description="Truck never came by our street.", **kw)
