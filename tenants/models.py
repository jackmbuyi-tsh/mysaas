from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.validators import RegexValidator
from django.db import models

from .context import get_current_tenant


class Tenant(models.Model):
    """One client of the platform: a school or a hotel."""

    class Kind(models.TextChoices):
        SCHOOL = "school", "École"
        HOTEL = "hotel", "Hôtel"

    name = models.CharField(max_length=200)
    subdomain = models.CharField(
        max_length=63,
        unique=True,
        validators=[
            RegexValidator(
                r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$",
                "Lowercase letters, digits and hyphens only.",
            )
        ],
    )
    kind = models.CharField(max_length=10, choices=Kind.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.subdomain})"


class MissingTenantError(ImproperlyConfigured):
    """Raised when tenant-scoped data is touched with no tenant set."""


class TenantManager(models.Manager):
    """
    Default manager for tenant-scoped models.

    Every query is filtered by the current tenant. If no tenant is set,
    the query fails loudly instead of silently returning all rows:
    leaking another client's data is the bug this project exists to prevent.
    """

    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant is None:
            raise MissingTenantError(
                f"No current tenant while querying {self.model.__name__}. "
                "Use tenant_context() or .unscoped for platform-level access."
            )
        return super().get_queryset().filter(tenant=tenant)


class TenantScopedModel(models.Model):
    """Base class for every table that belongs to one tenant."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="+", editable=False
    )

    objects = TenantManager()
    # Explicit escape hatch for platform admin and migrations.
    unscoped = models.Manager()

    class Meta:
        abstract = True
        base_manager_name = "unscoped"

    def save(self, *args, **kwargs):
        current = get_current_tenant()
        if self.tenant_id is None:
            if current is None:
                raise MissingTenantError(
                    f"Cannot save {type(self).__name__} without a tenant."
                )
            self.tenant = current
        elif current is not None and self.tenant_id != current.pk:
            raise MissingTenantError(
                f"Refusing to save {type(self).__name__} belonging to "
                f"tenant {self.tenant_id} while acting as tenant {current.pk}."
            )
        super().save(*args, **kwargs)


class Employee(TenantScopedModel):
    """Staff member of a school or a hotel."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employments",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    hired_on = models.DateField(null=True, blank=True)

    class Meta(TenantScopedModel.Meta):
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
