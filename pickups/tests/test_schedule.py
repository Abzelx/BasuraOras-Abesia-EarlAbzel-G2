from datetime import time

from django.db import IntegrityError, transaction
from django.urls import reverse

from pickups.models import CollectionSchedule

from .base import PickupTestCase


class ScheduleAccessTests(PickupTestCase):
    def test_anonymous_redirected_to_login(self):
        url = reverse("pickups:schedule_list")
        self.assertRedirects(self.client.get(url), f"{reverse('accounts:login')}?next={url}")

    def test_resident_gets_403(self):
        self.client.force_login(self.juan)
        for name in ("schedule_list", "schedule_create"):
            self.assertEqual(self.client.get(reverse(f"pickups:{name}")).status_code, 403)

    def test_staff_sees_only_own_barangay_schedules(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("pickups:schedule_list"))
        self.assertContains(response, "Rizal St")
        self.assertNotContains(response, "Luna St")


class ScheduleCrudTests(PickupTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)

    def data(self, **kw):
        d = {"street": self.street.pk, "day_of_week": 3, "start_time": "08:00", "end_time": "11:00", "is_active": "on"}
        d.update(kw)
        return d

    def test_create_sets_created_by(self):
        response = self.client.post(reverse("pickups:schedule_create"), self.data(), follow=True)
        self.assertRedirects(response, reverse("pickups:schedule_list"))
        schedule = CollectionSchedule.objects.get(street=self.street, day_of_week=3)
        self.assertEqual(schedule.created_by, self.staff)
        self.assertContains(response, "Schedule added")

    def test_duplicate_day_for_street_rejected(self):
        response = self.client.post(reverse("pickups:schedule_create"), self.data(day_of_week=1))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CollectionSchedule.objects.filter(street=self.street, day_of_week=1).count(), 1)

    def test_end_must_be_after_start(self):
        response = self.client.post(reverse("pickups:schedule_create"), self.data(start_time="10:00", end_time="09:00"))
        self.assertIn("end_time", response.context["form"].errors)

    def test_cannot_pick_street_of_another_barangay(self):
        response = self.client.post(reverse("pickups:schedule_create"), self.data(street=self.street_b.pk))
        self.assertIn("street", response.context["form"].errors)

    def test_required_fields(self):
        response = self.client.post(reverse("pickups:schedule_create"), {})
        for f in ("street", "day_of_week", "start_time", "end_time"):
            self.assertIn(f, response.context["form"].errors)

    def test_edit(self):
        url = reverse("pickups:schedule_edit", args=[self.monday.pk])
        self.client.post(url, self.data(day_of_week=1, start_time="06:00", end_time="09:00"))
        self.monday.refresh_from_db()
        self.assertEqual(self.monday.start_time, time(6, 0))

    def test_cannot_edit_other_barangays_schedule(self):
        self.assertEqual(self.client.get(reverse("pickups:schedule_edit", args=[self.sched_b.pk])).status_code, 404)

    def test_delete_unused_schedule(self):
        self.client.post(reverse("pickups:schedule_delete", args=[self.monday.pk]))
        self.assertFalse(CollectionSchedule.objects.filter(pk=self.monday.pk).exists())

    def test_delete_schedule_with_reports_only_deactivates(self):
        self.make_report()
        response = self.client.post(reverse("pickups:schedule_delete", args=[self.sunday.pk]), follow=True)
        self.sunday.refresh_from_db()
        self.assertFalse(self.sunday.is_active)
        self.assertContains(response, "deactivated instead of deleted")

    def test_delete_requires_post(self):
        self.assertEqual(self.client.get(reverse("pickups:schedule_delete", args=[self.monday.pk])).status_code, 405)

    def test_db_rejects_bad_day_number(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CollectionSchedule.objects.create(
                street=self.street2, day_of_week=9, start_time=time(7), end_time=time(8), created_by=self.staff)
