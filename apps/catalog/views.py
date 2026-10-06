from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.forms import TechnicianFilterForm, TechnicianForm
from apps.catalog.models import Technician


@login_required
def technician_list(request):
    if not request.user.has_perm("catalog.view_technician"):
        raise PermissionDenied

    technicians = Technician.objects.all()
    has_technicians = technicians.exists()
    filter_form = TechnicianFilterForm(request.GET or None)

    if filter_form.is_valid():
        q = filter_form.cleaned_data.get("q")
        if q:
            technicians = technicians.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(phone__icontains=q)
            )

        technician_type = filter_form.cleaned_data.get("technician_type")
        if technician_type:
            technicians = technicians.filter(technician_type=technician_type)

        active = filter_form.cleaned_data.get("active")
        if active == "1":
            technicians = technicians.filter(active=True)
        elif active == "0":
            technicians = technicians.filter(active=False)

    return render(
        request,
        "catalog/technician_list.html",
        {
            "technicians": technicians,
            "filter_form": filter_form,
            "has_technicians": has_technicians,
        },
    )


@login_required
def technician_detail(request, pk):
    if not request.user.has_perm("catalog.view_technician"):
        raise PermissionDenied

    technician = get_object_or_404(Technician, pk=pk)
    return render(
        request,
        "catalog/technician_detail.html",
        {"technician": technician},
    )


def _technician_form(request, *, technician=None):
    if request.method == "POST":
        form = TechnicianForm(request.POST, instance=technician)
        if form.is_valid():
            technician = form.save()
            return redirect("catalog:technician_detail", pk=technician.pk)
    else:
        form = TechnicianForm(instance=technician)

    return render(
        request,
        "catalog/technician_form.html",
        {
            "form": form,
            "technician": technician,
            "is_edit": technician is not None,
        },
    )


@login_required
def technician_create(request):
    if not request.user.has_perm("catalog.add_technician"):
        raise PermissionDenied

    return _technician_form(request)


@login_required
def technician_update(request, pk):
    if not request.user.has_perm("catalog.change_technician"):
        raise PermissionDenied

    technician = get_object_or_404(Technician, pk=pk)
    return _technician_form(request, technician=technician)


@login_required
@require_POST
def technician_toggle_active(request, pk):
    if not request.user.has_perm("catalog.change_technician"):
        raise PermissionDenied

    technician = get_object_or_404(Technician, pk=pk)
    technician.active = not technician.active
    technician.save(update_fields=["active"])
    return redirect("catalog:technician_detail", pk=technician.pk)
