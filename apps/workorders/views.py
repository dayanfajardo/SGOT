from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render

from apps.workorders.forms import WorkOrderCreateForm, WorkOrderItemFormSet
from apps.workorders.models import WorkOrder
from apps.workorders.services import create_work_order


@login_required
def work_order_list(request):
    if not request.user.has_perm("workorders.view_workorder"):
        raise PermissionDenied

    work_orders = WorkOrder.objects.select_related(
        "customer",
        "commercial",
        "work_type",
        "assigned_technician",
    )

    if request.user.groups.filter(name="Comercial").exists():
        work_orders = work_orders.filter(commercial=request.user)

    return render(
        request,
        "workorders/workorder_list.html",
        {"work_orders": work_orders},
    )


@login_required
def work_order_create(request):
    if not request.user.has_perm("workorders.add_workorder"):
        raise PermissionDenied

    if request.method == "POST":
        form = WorkOrderCreateForm(request.POST)
        formset = WorkOrderItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                work_order = create_work_order(
                    number=form.cleaned_data["number"],
                    customer=form.cleaned_data["customer"],
                    commercial=form.cleaned_data["commercial"],
                    work_type=form.cleaned_data["work_type"],
                    received_date=form.cleaned_data["received_date"],
                    created_by=request.user,
                    installation_address=form.cleaned_data["installation_address"],
                    notes=form.cleaned_data["notes"],
                )
                formset.instance = work_order
                formset.save()
            return redirect("workorders:workorder_list")
    else:
        form = WorkOrderCreateForm()
        formset = WorkOrderItemFormSet()

    return render(
        request,
        "workorders/workorder_form.html",
        {"form": form, "formset": formset},
    )
