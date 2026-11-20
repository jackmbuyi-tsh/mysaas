"""
Holds the tenant for the current request.

A ContextVar is used instead of a thread-local so it stays correct
under async views as well as threaded servers.
"""

from contextlib import contextmanager
from contextvars import ContextVar

_current_tenant = ContextVar("current_tenant", default=None)


def get_current_tenant():
    return _current_tenant.get()


def set_current_tenant(tenant):
    return _current_tenant.set(tenant)


def reset_current_tenant(token):
    _current_tenant.reset(token)


@contextmanager
def tenant_context(tenant):
    """Run a block of code as a given tenant (scripts, tests, jobs)."""
    token = set_current_tenant(tenant)
    try:
        yield tenant
    finally:
        reset_current_tenant(token)
