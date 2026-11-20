"""
Tenant isolation tests.

The original prototype had a bug where one school could see another
school's data. These tests make sure that can't come back.
"""

from datetime import date

from django.test import TestCase, override_settings

from schools.models import Pupil, SchoolClass, SchoolYear

from .context import tenant_context
from .middleware import subdomain_from_host
from .models import Employee, MissingTenantError, Tenant


class SubdomainParsingTests(TestCase):
    def test_parses_tenant_subdomain(self):
        self.assertEqual(subdomain_from_host("ecole1.localhost:8000", "localhost"), "ecole1")

    def test_bare_domain_has_no_tenant(self):
        self.assertIsNone(subdomain_from_host("localhost:8000", "localhost"))

    def test_nested_subdomain_rejected(self):
        self.assertIsNone(subdomain_from_host("a.b.localhost", "localhost"))

    def test_other_domain_rejected(self):
        self.assertIsNone(subdomain_from_host("ecole1.example.com", "localhost"))


class IsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school_a = Tenant.objects.create(name="École A", subdomain="ecole-a", kind="school")
        cls.school_b = Tenant.objects.create(name="École B", subdomain="ecole-b", kind="school")
        for tenant, name in [(cls.school_a, "Alice"), (cls.school_b, "Bob")]:
            with tenant_context(tenant):
                year = SchoolYear.objects.create(
                    label="2026-2027", starts_on=date(2026, 9, 1), ends_on=date(2027, 7, 2)
                )
                klass = SchoolClass.objects.create(name="6e A", year=year)
                Pupil.objects.create(first_name=name, last_name="Test", school_class=klass)
                Employee.objects.create(first_name=name, last_name="Prof", role="Enseignant")

    def test_each_tenant_sees_only_its_own_rows(self):
        with tenant_context(self.school_a):
            self.assertEqual(list(Pupil.objects.values_list("first_name", flat=True)), ["Alice"])
        with tenant_context(self.school_b):
            self.assertEqual(list(Pupil.objects.values_list("first_name", flat=True)), ["Bob"])

    def test_cannot_fetch_other_tenant_row_by_id(self):
        with tenant_context(self.school_b):
            bob_id = Pupil.objects.get().pk
        with tenant_context(self.school_a):
            with self.assertRaises(Pupil.DoesNotExist):
                Pupil.objects.get(pk=bob_id)

    def test_query_without_tenant_fails_loudly(self):
        with self.assertRaises(MissingTenantError):
            list(Pupil.objects.all())

    def test_save_without_tenant_fails(self):
        with self.assertRaises(MissingTenantError):
            Employee(first_name="X", last_name="Y", role="Z").save()

    def test_cannot_save_row_into_another_tenant(self):
        with tenant_context(self.school_b):
            bob = Pupil.objects.get()
        with tenant_context(self.school_a):
            bob.first_name = "Hacked"
            with self.assertRaises(MissingTenantError):
                bob.save()

    def test_unscoped_manager_sees_everything(self):
        self.assertEqual(Pupil.unscoped.count(), 2)


@override_settings(BASE_DOMAIN="localhost", ALLOWED_HOSTS=[".localhost", "localhost"])
class MiddlewareTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.school = Tenant.objects.create(name="École A", subdomain="ecole-a", kind="school")
        cls.hotel = Tenant.objects.create(name="Hôtel B", subdomain="hotel-b", kind="hotel")
        Tenant.objects.create(name="Old", subdomain="old", kind="school", is_active=False)

    def test_platform_home_on_bare_domain(self):
        response = self.client.get("/", HTTP_HOST="localhost")
        self.assertContains(response, "Plateforme de gestion")

    def test_tenant_home_shows_tenant(self):
        response = self.client.get("/", HTTP_HOST="ecole-a.localhost")
        self.assertContains(response, "École A")
        self.assertNotContains(response, "Hôtel B")

    def test_health_reports_tenant(self):
        response = self.client.get("/health/", HTTP_HOST="hotel-b.localhost")
        self.assertEqual(response.json()["tenant"], "hotel-b")

    def test_unknown_subdomain_404(self):
        response = self.client.get("/", HTTP_HOST="nope.localhost")
        self.assertEqual(response.status_code, 404)

    def test_inactive_tenant_404(self):
        response = self.client.get("/", HTTP_HOST="old.localhost")
        self.assertEqual(response.status_code, 404)
