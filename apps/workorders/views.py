from datetime import date, datetime
import re

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.workorders.forms import (
    WorkOrderCreateForm,
    WorkOrderItemFormSet,
    WorkOrderScheduleForm,
    WorkOrderStatusForm,
)
from apps.workorders.models import WorkOrder, WorkOrderHistory
from apps.workorders.services import (
    change_status,
    complete_work_order,
    create_work_order,
    schedule_work_order,
    start_installation,
)


_STATUS_LABELS = {
    WorkOrder.Status.RECEIVED: "Recibida",
    WorkOrder.Status.PENDING_EQUIPMENT: "Pendiente de equipos",
    WorkOrder.Status.EQUIPMENT_OK: "Equipos OK",
    WorkOrder.Status.IN_INSTALLATION: "En instalación",
    WorkOrder.Status.COMPLETED: "Completada",
}
_MONTHS_ES = {
    1: "ene",
    2: "feb",
    3: "mar",
    4: "abr",
    5: "may",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "sep",
    10: "oct",
    11: "nov",
    12: "dic",
}
_EMPTY_VALUES = {"", "none", "null", "—"}
_ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_STATUS_TOKEN_RE = re.compile(
    r"\b(RECEIVED|PENDING_EQUIPMENT|EQUIPMENT_OK|IN_INSTALLATION|COMPLETED)\b"
)
_NONE_TOKEN_RE = re.compile(r"\bNone\b")


def _format_date_es(value):
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        value = value.date()
    if isinstance(value, date):
        return f"{value.day} {_MONTHS_ES[value.month]} {value.year}"
    return None


def _format_datetime_es(value):
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return (
        f"{value.day} {_MONTHS_ES[value.month]} {value.year}, "
        f"{value:%H:%M}"
    )


def _parse_iso_date(text):
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt == "%Y-%m-%d":
            return parsed.date()
        return parsed
    return None


def _split_compound_value(raw):
    if raw is None:
        return "", ""
    text = str(raw)
    if " | " in text:
        left, right = text.split(" | ", 1)
        return left, right
    return text, ""


def _present_history_value(raw):
    if raw is None:
        return "—"

    text = str(raw).strip()
    if text.lower() in _EMPTY_VALUES:
        return "—"

    if " | " in text:
        left, right = _split_compound_value(text)
        parts = [
            part
            for part in (_present_history_value(left), _present_history_value(right))
            if part != "—"
        ]
        return " · ".join(parts) if parts else "—"

    if text in _STATUS_LABELS:
        return _STATUS_LABELS[text]

    parsed = _parse_iso_date(text)
    formatted = _format_date_es(parsed) if parsed is not None else None
    if formatted:
        return formatted

    return text


def _sanitize_description(text):
    if not text or str(text).strip().lower() in _EMPTY_VALUES:
        return "—"

    def replace_date(match):
        parsed = _parse_iso_date(match.group(1))
        formatted = _format_date_es(parsed) if parsed is not None else None
        return formatted or match.group(1)

    presented = _ISO_DATE_RE.sub(replace_date, str(text))
    presented = _STATUS_TOKEN_RE.sub(
        lambda match: _STATUS_LABELS.get(match.group(1), match.group(1)),
        presented,
    )
    presented = _NONE_TOKEN_RE.sub("—", presented)
    return re.sub(r"\s+", " ", presented).strip()


def _present_history_description(entry):
    event_type = entry.event_type
    previous = _present_history_value(entry.previous_value)
    new = _present_history_value(entry.new_value)

    if event_type == WorkOrderHistory.EventType.STATUS_CHANGED:
        return f"Estado cambiado de {previous} a {new}."

    if event_type == WorkOrderHistory.EventType.SCHEDULED:
        date_part, technician_part = _split_compound_value(entry.new_value)
        date_label = _present_history_value(date_part)
        technician_label = _present_history_value(technician_part)
        if date_label != "—" and technician_label != "—":
            return (
                f"Orden programada para el {date_label}. "
                f"Técnico: {technician_label}."
            )
        if date_label != "—":
            return f"Orden programada para el {date_label}."

    if event_type == WorkOrderHistory.EventType.RESCHEDULED:
        prev_date, prev_technician = _split_compound_value(entry.previous_value)
        new_date, new_technician = _split_compound_value(entry.new_value)
        prev_date_label = _present_history_value(prev_date)
        new_date_label = _present_history_value(new_date)
        prev_technician_label = _present_history_value(prev_technician)
        new_technician_label = _present_history_value(new_technician)
        if prev_date_label == "—" and new_date_label != "—":
            if new_technician_label != "—":
                return (
                    f"Orden programada para el {new_date_label}. "
                    f"Técnico: {new_technician_label}."
                )
            return f"Orden programada para el {new_date_label}."
        if new_date_label != "—":
            description = (
                f"Orden reprogramada del {prev_date_label} al {new_date_label}."
            )
            if (
                prev_technician_label != "—"
                or new_technician_label != "—"
            ):
                description += (
                    f" Técnico: {prev_technician_label} → {new_technician_label}."
                )
            return description

    if event_type == WorkOrderHistory.EventType.TECHNICIAN_CHANGED:
        return f"Técnico cambiado de {previous} a {new}."

    return _sanitize_description(entry.description)


def _history_presentation(entries):
    rows = []
    for entry in entries:
        rows.append(
            {
                "created_at": _format_datetime_es(entry.created_at),
                "event_type_label": entry.get_event_type_display(),
                "user": entry.user,
                "description": _present_history_description(entry),
                "previous_value": _present_history_value(entry.previous_value),
                "new_value": _present_history_value(entry.new_value),
            }
        )
    return rows


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
        "warehouse_output",
        "warehouse_output__technician",
        "warehouse_output__created_by",
        "warehouse_output__reconciled_by",
    ).prefetch_related(
        "items__product",
        "history__user",
        "warehouse_output__items__product",
        "warehouse_output__items__work_order_item",
        "warehouse_output__items__work_order_item__product",
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

    if "warehouse_output" not in context:
        context["warehouse_output"] = getattr(work_order, "warehouse_output", None)

    warehouse_output = context["warehouse_output"]

    if "can_create_warehouse_output" not in context:
        context["can_create_warehouse_output"] = (
            request.user.has_perm("warehouse.add_warehouseoutput")
            and work_order.status == WorkOrder.Status.EQUIPMENT_OK
            and work_order.assigned_technician_id is not None
            and warehouse_output is None
        )

    if "can_register_returns" not in context:
        context["can_register_returns"] = (
            warehouse_output is not None
            and warehouse_output.reconciled_at is None
            and request.user.has_perm("warehouse.change_warehouseoutput")
        )

    if "can_reconcile_warehouse_output" not in context:
        context["can_reconcile_warehouse_output"] = (
            warehouse_output is not None
            and warehouse_output.reconciled_at is None
            and work_order.status == WorkOrder.Status.IN_INSTALLATION
            and request.user.has_perm("warehouse.change_warehouseoutput")
        )

    if "can_complete_work_order" not in context:
        context["can_complete_work_order"] = (
            request.user.has_perm("workorders.change_workorder")
            and work_order.status == WorkOrder.Status.IN_INSTALLATION
            and warehouse_output is not None
            and warehouse_output.reconciled_at is not None
        )


def _render_work_order_detail(request, work_order, extra_context=None):
    context = {
        "work_order": work_order,
        "history_entries": _history_presentation(work_order.history.all()),
    }
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


@login_required
@require_POST
def work_order_complete(request, pk):
    if not request.user.has_perm("workorders.change_workorder"):
        raise PermissionDenied

    work_order = get_object_or_404(WorkOrder, pk=pk)

    try:
        complete_work_order(
            work_order=work_order,
            actor=request.user,
        )
    except ValidationError as exc:
        return _render_work_order_detail(
            request,
            work_order,
            {"complete_work_order_error": exc.messages},
        )

    return redirect("workorders:workorder_detail", pk=work_order.pk)
