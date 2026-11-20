from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "subdomain", "kind", "is_active", "created_at")
    list_filter = ("kind", "is_active")
    search_fields = ("name", "subdomain")
