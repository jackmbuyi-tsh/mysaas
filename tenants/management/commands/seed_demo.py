from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from hotels.models import Room
from schools.models import Pupil, SchoolClass, SchoolYear
from tenants.context import tenant_context
from tenants.models import Employee, Tenant


class Command(BaseCommand):
    help = "Create two demo schools and one demo hotel."

    @transaction.atomic
    def handle(self, *args, **options):
        for sub, name in [("ecole1", "École Uzuri 1"), ("ecole2", "École Uzuri 2")]:
            tenant, created = Tenant.objects.get_or_create(
                subdomain=sub, defaults={"name": name, "kind": Tenant.Kind.SCHOOL}
            )
            if created:
                with tenant_context(tenant):
                    year = SchoolYear.objects.create(
                        label="2026-2027", starts_on=date(2026, 9, 1), ends_on=date(2027, 7, 2)
                    )
                    klass = SchoolClass.objects.create(name="6e A", year=year)
                    Employee.objects.create(first_name="Prof", last_name=sub, role="Enseignant")
                    for i in range(1, 4):
                        Pupil.objects.create(
                            first_name=f"Élève {i}", last_name=sub, school_class=klass
                        )

        hotel, created = Tenant.objects.get_or_create(
            subdomain="hotel1", defaults={"name": "Hôtel Uzuri", "kind": Tenant.Kind.HOTEL}
        )
        if created:
            with tenant_context(hotel):
                Employee.objects.create(first_name="Réception", last_name="1", role="Réceptionniste")
                for n in ["101", "102", "201"]:
                    Room.objects.create(number=n, room_type="double", nightly_rate=Decimal("50.00"))

        self.stdout.write(self.style.SUCCESS(
            "Demo data ready: ecole1.localhost:8000, ecole2.localhost:8000, hotel1.localhost:8000"
        ))
