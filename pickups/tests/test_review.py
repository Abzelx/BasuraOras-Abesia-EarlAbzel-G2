from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from pickups.models import MissedReport

from .base import PickupTestCase


class StaffReviewTests(PickupTestCase):
    def setUp(self):
        super().setUp()
        self.report = self.make_report()
        self.url = reverse("pickups:staff_report_review", args=[self.report.pk])
        self.client.force_login(self.staff)

    def test_resident_cannot_open_staff_pages(self):
        self.client.force_login(self.juan)
        self.assertEqual(self.client.get(reverse("pickups:staff_report_list")).status_code, 403)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_staff_list_only_own_barangay(self):
        other = self.make_report(user=self.juan, schedule=self.sched_b)  # (data only; juan is not in B)
        response = self.client.get(reverse("pickups:staff_report_list"))
        self.assertContains(response, f"#{self.report.pk}</a>")
        self.assertNotContains(response, f"#{other.pk}</a>")

    def test_staff_of_other_barangay_gets_404(self):
        self.client.force_login(self.staff_b)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, {"status": "ACKNOWLEDGED"}).status_code, 404)

    def test_acknowledge(self):
        response = self.client.post(self.url, {"status": "ACKNOWLEDGED", "staff_response": "Truck will return."}, follow=True)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "ACKNOWLEDGED")
        self.assertEqual(self.report.handled_by, self.staff)
        self.assertIsNone(self.report.resolved_at)
        self.assertContains(response, "marked as Acknowledged")

    def test_resolve_records_handler_and_time(self):
        self.report.status = "ACKNOWLEDGED"
        self.report.save()
        self.client.post(self.url, {"status": "RESOLVED", "staff_response": "Collected this morning."})
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "RESOLVED")
        self.assertEqual(self.report.handled_by, self.staff)
        self.assertIsNotNone(self.report.resolved_at)

    def test_cannot_skip_acknowledged(self):
        response = self.client.post(self.url, {"status": "RESOLVED", "staff_response": "done"})
        self.assertIn("status", response.context["form"].errors)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "SUBMITTED")

    def test_dismiss_requires_response(self):
        response = self.client.post(self.url, {"status": "DISMISSED", "staff_response": "  "})
        self.assertIn("staff_response", response.context["form"].errors)

    def test_dismiss_with_response(self):
        self.client.post(self.url, {"status": "DISMISSED", "staff_response": "Truck did come at 6:55 AM."})
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "DISMISSED")

    def test_final_report_cannot_change(self):
        self.report.status = "DISMISSED"
        self.report.staff_response = "No."
        self.report.handled_by = self.staff
        self.report.resolved_at = timezone.now()
        self.report.save()
        self.client.post(self.url, {"status": "ACKNOWLEDGED"})
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "DISMISSED")

    def test_db_rejects_resolved_without_handler(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            MissedReport.objects.filter(pk=self.report.pk).update(status="RESOLVED")

    def test_db_rejects_dismissed_without_response(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            MissedReport.objects.filter(pk=self.report.pk).update(
                status="DISMISSED", handled_by=self.staff, resolved_at=timezone.now())


class DashboardIntegrationTests(PickupTestCase):
    def test_resident_dashboard_shows_next_collection_and_reports(self):
        self.make_report()
        self.client.force_login(self.juan)
        response = self.client.get(reverse("accounts:resident_dashboard"))
        self.assertContains(response, "Monday, Nov 16")  # today is Monday and Rizal St is collected Mondays
        self.assertContains(response, "Report a missed collection")

    def test_staff_dashboard_counts_new_reports(self):
        self.make_report()
        self.client.force_login(self.staff)
        response = self.client.get(reverse("accounts:staff_dashboard"))
        self.assertEqual(response.context["pending_count"], 1)

    def test_nav_links_follow_role(self):
        self.client.force_login(self.juan)
        page = self.client.get(reverse("accounts:resident_dashboard"))
        self.assertContains(page, "My Reports")
        self.assertNotContains(page, "Schedules</a>")
        self.client.force_login(self.staff)
        page = self.client.get(reverse("accounts:staff_dashboard"))
        self.assertContains(page, "Schedules</a>")
