from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from apps.warehouse.forms import (
    WarehouseOutputCreateForm,
    WarehouseOutputItemFormSet,
)
from apps.warehouse.models import WarehouseOutput
from apps.warehouse.services import add_output_item, create_warehouse_output
from apps.workorders.models import WorkOrder


@login_required
def warehouse_output_create(request, work_order_pk):
    if not request.user.has_perm("warehouse.add_warehouseoutput"):
        raise PermissionDenied

    work_order = get_object_or_404(WorkOrder, pk=work_order_pk)
    output_instance = WarehouseOutput()

    if request.method == "POST":
        form = WarehouseOutputCreateForm(request.POST)
        formset = WarehouseOutputItemFormSet(
            request.POST,
            instance=output_instance,
            form_kwargs={"work_order": work_order},
        )
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    warehouse_output = create_warehouse_output(
                        number=form.cleaned_data["number"],
                        work_order=work_order,
                        technician=work_order.assigned_technician,
                        output_date=form.cleaned_data["output_date"],
                        created_by=request.user,
                        notes=form.cleaned_data["notes"],
                    )
                    for item_form in formset:
                        if not item_form.has_changed():
                            continue
                        if item_form.cleaned_data.get("DELETE"):
                            continue
                        add_output_item(
                            warehouse_output=warehouse_output,
                            product=item_form.cleaned_data["product"],
                            work_order_item=item_form.cleaned_data.get(
                                "work_order_item"
                            ),
                            delivered_quantity=item_form.cleaned_data[
                                "delivered_quantity"
                            ],
                            notes=item_form.cleaned_data["notes"],
                        )
            except ValidationError as exc:
                form.add_error(None, exc)
            else:
                return redirect(
                    "workorders:workorder_detail",
                    pk=work_order.pk,
                )
    else:
        form = WarehouseOutputCreateForm()
        formset = WarehouseOutputItemFormSet(
            instance=output_instance,
            form_kwargs={"work_order": work_order},
        )

    return render(
        request,
        "warehouse/warehouse_output_form.html",
        {
            "form": form,
            "formset": formset,
            "work_order": work_order,
        },
    )
