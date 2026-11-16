from datetime import timedelta

from django.urls import reverse

from pickups.models import MissedReport

from .base import FAKE_TODAY, YESTERDAY, PickupTestCase


class ReportCreateTests(PickupTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.juan)
        self.url = reverse("pickups:report_create")

    def post(self, **kw):
        data = {"schedule": self.sunday.pk, "collection_date": YESTERDAY.isoformat(),
                "description": "The truck never came to our street."}
        data.update(kw)
        return self.client.post(self.url, data)

    def test_create_links_report_to_logged_in_user(self):
        response = self.post()
        report = MissedReport.objects.get()
        self.assertRedirects(response, reverse("pickups:report_detail", args=[report.pk]))
        self.assertEqual(report.user, self.juan)
        self.assertEqual(report.status, MissedReport.Status.SUBMITTED)

    def test_success_message_shown(self):
        response = self.client.post(self.url, {
            "schedule": self.sunday.pk, "collection_date": YESTERDAY.isoformat(),
            "description": "The truck never came to our street."}, follow=True)
        self.assertContains(response, "report was submitted")

    def test_required_fields(self):
        response = self.client.post(self.url, {})
        for f in ("schedule", "collection_date", "description"):
            self.assertIn(f, response.context["form"].errors)

    def test_description_too_short(self):
        self.assertIn("description", self.post(description="no").context["form"].errors)

    def test_future_date_rejected(self):
        response = self.post(collection_date=(FAKE_TODAY + timedelta(days=1)).isoformat())
        self.assertIn("collection_date", response.context["form"].errors)

    def test_older_than_7_days_rejected(self):
        old = YESTERDAY - timedelta(days=7)  # still a Sunday, but 8 days ago
        self.assertIn("collection_date", self.post(collection_date=old.isoformat()).context["form"].errors)

    def test_date_must_match_schedule_weekday(self):
        wrong = YESTERDAY - timedelta(days=1)  # a Saturday, but the schedule is Sunday
        response = self.post(collection_date=wrong.isoformat())
        self.assertContains(response, "is collected on Sundays")

    def test_today_allowed_after_collection_window_ended(self):
        # frozen time is 3 PM and the window ended at 10 AM -> allowed
        self.assertEqual(self.post(schedule=self.monday.pk, collection_date=FAKE_TODAY.isoformat()).status_code, 302)

    def test_today_rejected_if_window_not_over(self):
        from datetime import time
        self.monday.end_time = time(18, 0)
        self.monday.save()
        response = self.post(schedule=self.monday.pk, collection_date=FAKE_TODAY.isoformat())
        self.assertContains(response, "window ends at")
        self.assertEqual(MissedReport.objects.count(), 0)

    def test_duplicate_report_rejected(self):
        self.make_report()
        response = self.post()
        self.assertContains(response, "already reported this collection")
        self.assertEqual(MissedReport.objects.count(), 1)

    def test_schedule_of_another_street_not_allowed(self):
        response = self.post(schedule=self.mabini_sunday.pk)
        self.assertIn("schedule", response.context["form"].errors)

    def test_inactive_schedule_not_allowed(self):
        self.sunday.is_active = False
        self.sunday.save()
        self.assertIn("schedule", self.post().context["form"].errors)

    def test_max_three_reports_in_24_hours(self):
        # Three reports already filed "just now" (different schedule/date combinations)
        self.make_report(schedule=self.sunday, when=YESTERDAY - timedelta(days=7))
        self.make_report(schedule=self.sunday, when=YESTERDAY - timedelta(days=14))
        self.make_report(schedule=self.sunday, when=YESTERDAY - timedelta(days=21))
        response = self.post()
        self.assertContains(response, "at most 3 reports")
        self.assertEqual(MissedReport.objects.count(), 3)

    def test_staff_cannot_open_report_form(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonymous_redirected(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)


class ReportReadUpdateTests(PickupTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.juan)
        self.report = self.make_report()

    def test_list_shows_only_own_reports(self):
        mine = self.make_report(user=self.maria, schedule=self.mabini_sunday)
        response = self.client.get(reverse("pickups:report_list"))
        self.assertContains(response, f"#{self.report.pk}")
        self.assertNotContains(response, f"#{mine.pk}</a>")

    def test_status_filter(self):
        response = self.client.get(reverse("pickups:report_list"), {"status": "RESOLVED"})
        self.assertNotContains(response, f"#{self.report.pk}</a>")

    def test_detail_of_own_report(self):
        self.assertContains(self.client.get(reverse("pickups:report_detail", args=[self.report.pk])), "Truck never came")

    def test_cannot_view_someone_elses_report(self):
        other = self.make_report(user=self.maria, schedule=self.mabini_sunday)
        self.assertEqual(self.client.get(reverse("pickups:report_detail", args=[other.pk])).status_code, 404)

    def test_cannot_edit_someone_elses_report(self):
        other = self.make_report(user=self.maria, schedule=self.mabini_sunday)
        self.assertEqual(self.client.post(reverse("pickups:report_edit", args=[other.pk]),
                                          {"description": "hacked by juan!"}).status_code, 404)
        other.refresh_from_db()
        self.assertNotIn("hacked", other.description)

    def test_edit_description_while_submitted(self):
        self.client.post(reverse("pickups:report_edit", args=[self.report.pk]),
                         {"description": "Updated: the truck skipped us again."})
        self.report.refresh_from_db()
        self.assertIn("Updated", self.report.description)

    def test_edit_cannot_change_status(self):
        self.client.post(reverse("pickups:report_edit", args=[self.report.pk]),
                         {"description": "Updated text for report.", "status": "RESOLVED"})
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, MissedReport.Status.SUBMITTED)

    def test_edit_blocked_after_staff_responds(self):
        self.report.status = MissedReport.Status.ACKNOWLEDGED
        self.report.save()
        response = self.client.post(reverse("pickups:report_edit", args=[self.report.pk]),
                                    {"description": "Trying to edit after review."}, follow=True)
        self.assertContains(response, "can no longer be edited")
        self.report.refresh_from_db()
        self.assertNotIn("Trying", self.report.description)
