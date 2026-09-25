from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.workorders.forms import (
    WorkOrderCreateForm,
    WorkOrderItemFormSet,
    WorkOrderScheduleForm,
    WorkOrderStatusForm,
)
from apps.workorders.models import WorkOrder
from apps.workorders.services import (
    change_status,
    create_work_order,
    schedule_work_order,
    start_installation,
)


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


@login_required
def work_order_detail(request, pk):
    if not request.user.has_perm("workorders.view_workorder"):
        raise PermissionDenied

    work_orders = WorkOrder.objects.select_related(
        "customer",
        "commercial",
        "work_type",
        "assigned_technician",
        "created_by",
    ).prefetch_related(
        "items__product",
        "history__user",
    )

    if request.user.groups.filter(name="Comercial").exists():
        work_orders = work_orders.filter(commercial=request.user)

    work_order = get_object_or_404(work_orders, pk=pk)

    return _render_work_order_detail(request, work_order)


def _ensure_detail_action_forms(request, work_order, context):
    if "schedule_form" not in context:
        if (
            request.user.has_perm("workorders.schedule_workorder")
            and work_order.status == WorkOrder.Status.EQUIPMENT_OK
        ):
            context["schedule_form"] = WorkOrderScheduleForm(work_order=work_order)

    if "status_form" not in context:
        if request.user.has_perm("workorders.change_workorder"):
            status_form = WorkOrderStatusForm(work_order=work_order)
            if status_form.fields["new_status"].choices:
                context["status_form"] = status_form

    if "can_start_installation" not in context:
        context["can_start_installation"] = (
            request.user.has_perm("workorders.change_workorder")
            and work_order.status == WorkOrder.Status.EQUIPMENT_OK
            and work_order.assigned_technician_id
            and work_order.scheduled_date
        )


def _render_work_order_detail(request, work_order, extra_context=None):
    context = {"work_order": work_order}
    if extra_context:
        context.update(extra_context)
    _ensure_detail_action_forms(request, work_order, context)
    return render(request, "workorders/workorder_detail.html", context)


@login_required
@require_POST
def work_order_schedule(request, pk):
    if not request.user.has_perm("workorders.schedule_workorder"):
        raise PermissionDenied

    work_order = get_object_or_404(WorkOrder, pk=pk)
    form = WorkOrderScheduleForm(request.POST, work_order=work_order)

    if form.is_valid():
        try:
            schedule_work_order(
                work_order=work_order,
                technician=form.cleaned_data["technician"],
                scheduled_date=form.cleaned_data["scheduled_date"],
                actor=request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("workorders:workorder_detail", pk=work_order.pk)

    return _render_work_order_detail(
        request,
        work_order,
        {"schedule_form": form},
    )


@login_required
@require_POST
def work_order_change_status(request, pk):
    if not request.user.has_perm("workorders.change_workorder"):
        raise PermissionDenied

    work_order = get_object_or_404(WorkOrder, pk=pk)
    form = WorkOrderStatusForm(request.POST, work_order=work_order)

    if form.is_valid():
        try:
            change_status(
                work_order=work_order,
                new_status=form.cleaned_data["new_status"],
                actor=request.user,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("workorders:workorder_detail", pk=work_order.pk)

    return _render_work_order_detail(
        request,
        work_order,
        {"status_form": form},
    )


@login_required
@require_POST
def work_order_start_installation(request, pk):
    if not request.user.has_perm("workorders.change_workorder"):
        raise PermissionDenied

    work_order = get_object_or_404(WorkOrder, pk=pk)

    try:
        start_installation(
            work_order=work_order,
            actor=request.user,
        )
    except ValidationError as exc:
        return _render_work_order_detail(
            request,
            work_order,
            {"start_installation_error": exc.messages},
        )

    return redirect("workorders:workorder_detail", pk=work_order.pk)
