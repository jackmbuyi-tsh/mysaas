from django.http import JsonResponse
from django.shortcuts import render

from hotels.models import Reservation, Room
from schools.models import Pupil, SchoolClass

from .models import Employee, Tenant


def home(request):
    tenant = request.tenant
    if tenant is None:
        return render(request, "platform_home.html")

    stats = {"employees": Employee.objects.count()}
    if tenant.kind == Tenant.Kind.SCHOOL:
        stats.update(classes=SchoolClass.objects.count(), pupils=Pupil.objects.count())
    else:
        stats.update(rooms=Room.objects.count(), reservations=Reservation.objects.count())
    return render(request, "tenant_home.html", {"stats": stats})


def health(request):
    return JsonResponse({"status": "ok", "tenant": getattr(request.tenant, "subdomain", None)})
