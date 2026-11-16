from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from locations.models import Barangay, Street

GOOD_PASSWORD = "Garbage2026x"


class BaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.barangay = Barangay.objects.create(name="Test Barangay")
        cls.street = Street.objects.create(barangay=cls.barangay, name="Rizal St", purok="Purok 1")
        cls.street2 = Street.objects.create(barangay=cls.barangay, name="Mabini St", purok="Purok 2")
        cls.resident = User.objects.create_user(
            username="juan", email="juan@example.com", password=GOOD_PASSWORD,
            first_name="Juan", last_name="Cruz", role=User.Role.RESIDENT, street=cls.street,
        )
        cls.other_resident = User.objects.create_user(
            username="maria", email="maria@example.com", password=GOOD_PASSWORD,
            first_name="Maria", last_name="Santos", role=User.Role.RESIDENT, street=cls.street2,
        )
        cls.staff = User.objects.create_user(
            username="staff1", email="staff1@example.com", password=GOOD_PASSWORD,
            first_name="Sam", last_name="Staff", role=User.Role.STAFF, barangay=cls.barangay,
        )

    def registration_data(self, **overrides):
        data = {
            "username": "newuser", "first_name": "New", "last_name": "User",
            "email": "new@example.com", "phone_number": "09171234567",
            "street": self.street.pk, "password1": GOOD_PASSWORD, "password2": GOOD_PASSWORD,
        }
        data.update(overrides)
        return data


class RegistrationTests(BaseTestCase):
    def test_successful_registration_creates_hashed_resident_and_logs_in(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data(), follow=True)
        user = User.objects.get(username="newuser")
        self.assertEqual(user.role, User.Role.RESIDENT)
        self.assertNotEqual(user.password, GOOD_PASSWORD)          # never plain text
        self.assertTrue(user.password.startswith("pbkdf2_"))        # Django's hasher
        self.assertTrue(user.check_password(GOOD_PASSWORD))
        self.assertRedirects(response, reverse("accounts:resident_dashboard"))
        self.assertContains(response, "Your account has been created")

    def test_required_fields(self):
        response = self.client.post(reverse("accounts:register"), {})
        for field in ("username", "first_name", "last_name", "email", "street", "password1", "password2"):
            self.assertIn(field, response.context["form"].errors)
        self.assertEqual(User.objects.count(), 3)

    def test_invalid_email_format(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data(email="not-an-email"))
        self.assertIn("email", response.context["form"].errors)

    def test_duplicate_username_rejected_case_insensitively(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data(username="JUAN"))
        self.assertIn("username", response.context["form"].errors)

    def test_duplicate_email_rejected_case_insensitively(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data(email="JUAN@example.com"))
        self.assertIn("email", response.context["form"].errors)

    def test_password_confirmation_must_match(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data(password2="Different123"))
        self.assertIn("password2", response.context["form"].errors)

    def test_password_needs_letter_and_number(self):
        response = self.client.post(
            reverse("accounts:register"),
            self.registration_data(password1="onlyletterspassword", password2="onlyletterspassword"),
        )
        self.assertIn("password2", response.context["form"].errors)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_password_min_length(self):
        response = self.client.post(
            reverse("accounts:register"), self.registration_data(password1="ab1", password2="ab1"))
        self.assertIn("password2", response.context["form"].errors)

    def test_invalid_phone_number(self):
        response = self.client.post(reverse("accounts:register"), self.registration_data(phone_number="12345"))
        self.assertIn("phone_number", response.context["form"].errors)

    def test_inactive_barangay_street_not_allowed(self):
        inactive = Barangay.objects.create(name="Closed", is_active=False)
        street = Street.objects.create(barangay=inactive, name="Hidden St")
        response = self.client.post(reverse("accounts:register"), self.registration_data(street=street.pk))
        self.assertIn("street", response.context["form"].errors)

    def test_cannot_register_as_staff_by_posting_role(self):
        self.client.post(reverse("accounts:register"), self.registration_data(role="STAFF"))
        self.assertEqual(User.objects.get(username="newuser").role, User.Role.RESIDENT)


class LoginLogoutTests(BaseTestCase):
    def test_login_with_username(self):
        response = self.client.post(reverse("accounts:login"), {"username": "juan", "password": GOOD_PASSWORD}, follow=True)
        self.assertRedirects(response, reverse("accounts:resident_dashboard"))

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "JUAN@example.com", "password": GOOD_PASSWORD}, follow=True)
        self.assertRedirects(response, reverse("accounts:resident_dashboard"))

    def test_invalid_credentials_show_error(self):
        response = self.client.post(reverse("accounts:login"), {"username": "juan", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username/email or password")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_ends_session(self):
        self.client.force_login(self.resident)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(self.resident)
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)

    def test_protected_pages_redirect_anonymous_to_login(self):
        for name in ("dashboard", "resident_dashboard", "staff_dashboard", "profile", "profile_edit"):
            url = reverse(f"accounts:{name}")
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}", msg_prefix=name)


class RoleDashboardTests(BaseTestCase):
    def test_resident_redirected_to_resident_dashboard(self):
        self.client.force_login(self.resident)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard")), reverse("accounts:resident_dashboard"))

    def test_staff_redirected_to_staff_dashboard(self):
        self.client.force_login(self.staff)
        self.assertRedirects(self.client.get(reverse("accounts:dashboard")), reverse("accounts:staff_dashboard"))

    def test_resident_cannot_open_staff_dashboard(self):
        self.client.force_login(self.resident)
        self.assertEqual(self.client.get(reverse("accounts:staff_dashboard")).status_code, 403)

    def test_staff_cannot_open_resident_dashboard(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse("accounts:resident_dashboard")).status_code, 403)

    def test_dashboards_show_role_content(self):
        self.client.force_login(self.resident)
        self.assertContains(self.client.get(reverse("accounts:resident_dashboard")), "Next collection")
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse("accounts:staff_dashboard")), "Post an advisory")


class ProfileTests(BaseTestCase):
    def test_profile_shows_own_details_only(self):
        self.client.force_login(self.resident)
        response = self.client.get(reverse("accounts:profile"))
        self.assertContains(response, "juan@example.com")
        self.assertNotContains(response, "maria@example.com")

    def test_update_profile(self):
        self.client.force_login(self.resident)
        response = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Juanito", "last_name": "Cruz", "email": "juanito@example.com",
            "phone_number": "+639181112222", "street": self.street2.pk, "house_details": "Blue gate",
        }, follow=True)
        self.assertRedirects(response, reverse("accounts:profile"))
        self.resident.refresh_from_db()
        self.assertEqual(self.resident.first_name, "Juanito")
        self.assertEqual(self.resident.street, self.street2)
        self.assertContains(response, "Your profile has been updated")

    def test_cannot_use_someone_elses_email(self):
        self.client.force_login(self.resident)
        response = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Juan", "last_name": "Cruz", "email": "MARIA@example.com", "street": self.street.pk,
        })
        self.assertIn("email", response.context["form"].errors)

    def test_keeping_own_email_is_fine(self):
        self.client.force_login(self.resident)
        response = self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Juan", "last_name": "Cruz", "email": "juan@example.com", "street": self.street.pk,
        })
        self.assertRedirects(response, reverse("accounts:profile"))

    def test_edit_cannot_change_role_or_username(self):
        self.client.force_login(self.resident)
        self.client.post(reverse("accounts:profile_edit"), {
            "first_name": "Juan", "last_name": "Cruz", "email": "juan@example.com",
            "street": self.street.pk, "role": "STAFF", "username": "hacker", "is_superuser": "on",
        })
        self.resident.refresh_from_db()
        self.assertEqual(self.resident.role, User.Role.RESIDENT)
        self.assertEqual(self.resident.username, "juan")
        self.assertFalse(self.resident.is_superuser)

    def test_staff_edit_form_has_position_not_street(self):
        self.client.force_login(self.staff)
        form = self.client.get(reverse("accounts:profile_edit")).context["form"]
        self.assertIn("position_title", form.fields)
        self.assertNotIn("street", form.fields)
