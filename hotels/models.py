from django.db import models

from tenants.models import Employee, TenantScopedModel


class Room(TenantScopedModel):
    number = models.CharField(max_length=10)
    room_type = models.CharField(max_length=50)  # single, double, suite...
    nightly_rate = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta(TenantScopedModel.Meta):
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "number"], name="unique_room_per_hotel")
        ]

    def __str__(self):
        return f"Chambre {self.number}"


class Guest(TenantScopedModel):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.full_name


class Reservation(TenantScopedModel):
    class Status(models.TextChoices):
        BOOKED = "booked", "Réservée"
        CHECKED_IN = "checked_in", "Arrivée"
        CHECKED_OUT = "checked_out", "Départ"
        CANCELLED = "cancelled", "Annulée"

    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="reservations")
    guest = models.ForeignKey(Guest, on_delete=models.PROTECT, related_name="reservations")
    check_in = models.DateField()
    check_out = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)
    handled_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="reservations"
    )

    def __str__(self):
        return f"{self.guest} – {self.room} ({self.check_in} → {self.check_out})"


class Invoice(TenantScopedModel):
    reservation = models.ForeignKey(Reservation, on_delete=models.PROTECT, related_name="invoices")
    issued_on = models.DateField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)  # payments come after the first release

    def __str__(self):
        return f"Facture #{self.pk} – {self.total}"


class Expense(TenantScopedModel):
    label = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    spent_on = models.DateField()
    category = models.CharField(max_length=50, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["-spent_on"]

    def __str__(self):
        return f"{self.label} – {self.amount}"
