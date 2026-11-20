from django.conf import settings
from django.http import Http404

from .context import reset_current_tenant, set_current_tenant
from .models import Tenant


def subdomain_from_host(host, base_domain):
    """'ecole1.localhost:8000' -> 'ecole1'; the bare domain -> None."""
    host = host.split(":")[0].lower()
    base_domain = base_domain.lower()
    if host == base_domain or not host.endswith("." + base_domain):
        return None
    sub = host[: -(len(base_domain) + 1)]
    # Only one level: a.b.localhost is not a valid tenant host.
    return sub if sub and "." not in sub else None


class TenantMiddleware:
    """
    Resolves the tenant from the request's subdomain.

    - bare domain (localhost): platform pages, no tenant
    - known active subdomain: request.tenant is set and all
      TenantScopedModel queries are filtered to it
    - unknown or inactive subdomain: 404
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        sub = subdomain_from_host(request.get_host(), settings.BASE_DOMAIN)
        tenant = None
        if sub is not None:
            tenant = Tenant.objects.filter(subdomain=sub, is_active=True).first()
            if tenant is None:
                raise Http404("Unknown tenant")

        request.tenant = tenant
        token = set_current_tenant(tenant)
        try:
            return self.get_response(request)
        finally:
            reset_current_tenant(token)
