from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import WorkOrder, WorkOrderHistory

ALLOWED_STATUS_TRANSITIONS = {
    WorkOrder.Status.RECEIVED: {
        WorkOrder.Status.PENDING_EQUIPMENT,
        WorkOrder.Status.EQUIPMENT_OK,
    },
    WorkOrder.Status.PENDING_EQUIPMENT: {
        WorkOrder.Status.EQUIPMENT_OK,
    },
}


def _create_history(
    *,
    work_order,
    actor,
    event_type,
    description,
    previous_value="",
    new_value="",
):
    WorkOrderHistory.objects.create(
        work_order=work_order,
        user=actor,
        event_type=event_type,
        description=description,
        previous_value=previous_value,
        new_value=new_value,
    )


@transaction.atomic
def change_status(*, work_order, new_status, actor):
    current_status = work_order.status

    if new_status == current_status:
        raise ValidationError("El nuevo estado debe ser diferente al estado actual.")

    allowed = ALLOWED_STATUS_TRANSITIONS.get(current_status, set())
    if new_status not in allowed:
        raise ValidationError("La transición de estado no está permitida.")

    work_order.status = new_status
    work_order.save()

    _create_history(
        work_order=work_order,
        actor=actor,
        event_type=WorkOrderHistory.EventType.STATUS_CHANGED,
        description=(
            f"Estado cambiado de {current_status} a {new_status}."
        ),
        previous_value=current_status,
        new_value=new_status,
    )
    return work_order


@transaction.atomic
def schedule_work_order(*, work_order, technician, scheduled_date, actor):
    if work_order.status != WorkOrder.Status.EQUIPMENT_OK:
        raise ValidationError(
            "Solo se puede programar una orden en estado Equipos OK."
        )

    if technician is None:
        raise ValidationError("Se debe seleccionar un técnico.")

    if scheduled_date is None:
        raise ValidationError("Se debe indicar una fecha de programación.")

    if not technician.active:
        raise ValidationError("El técnico debe estar activo.")

    current_technician = work_order.assigned_technician
    current_date = work_order.scheduled_date
    same_technician = work_order.assigned_technician_id == technician.pk
    same_date = current_date == scheduled_date

    if same_technician and same_date:
        raise ValidationError("No hay cambios en la programación de la orden.")

    is_first_schedule = current_date is None and current_technician is None

    work_order.assigned_technician = technician
    work_order.scheduled_date = scheduled_date
    work_order.save()

    if is_first_schedule:
        _create_history(
            work_order=work_order,
            actor=actor,
            event_type=WorkOrderHistory.EventType.SCHEDULED,
            description=(
                f"Orden programada para el {scheduled_date} "
                f"con el técnico {technician}."
            ),
            previous_value="",
            new_value=f"{scheduled_date} | {technician}",
        )
    elif not same_date:
        previous_technician = current_technician or "Sin técnico"
        _create_history(
            work_order=work_order,
            actor=actor,
            event_type=WorkOrderHistory.EventType.RESCHEDULED,
            description=(
                f"Orden reprogramada del {current_date} al {scheduled_date}. "
                f"Técnico: {previous_technician} -> {technician}."
            ),
            previous_value=f"{current_date} | {previous_technician}",
            new_value=f"{scheduled_date} | {technician}",
        )
    else:
        _create_history(
            work_order=work_order,
            actor=actor,
            event_type=WorkOrderHistory.EventType.TECHNICIAN_CHANGED,
            description=(
                f"Técnico cambiado de {current_technician} a {technician}."
            ),
            previous_value=str(current_technician),
            new_value=str(technician),
        )

    return work_order


@transaction.atomic
def start_installation(*, work_order, actor):
    if work_order.status != WorkOrder.Status.EQUIPMENT_OK:
        raise ValidationError(
            "Solo se puede iniciar la instalación si la orden está en Equipos OK."
        )

    if not work_order.assigned_technician or not work_order.scheduled_date:
        raise ValidationError(
            "La orden debe tener técnico asignado y fecha programada."
        )

    previous_status = work_order.status
    work_order.status = WorkOrder.Status.IN_INSTALLATION
    work_order.installation_started_at = timezone.now()
    work_order.save()

    _create_history(
        work_order=work_order,
        actor=actor,
        event_type=WorkOrderHistory.EventType.INSTALLATION_STARTED,
        description="Se inició la instalación.",
        previous_value=previous_status,
        new_value=work_order.status,
    )
    return work_order


@transaction.atomic
def complete_work_order(*, work_order, actor):
    if work_order.status != WorkOrder.Status.IN_INSTALLATION:
        raise ValidationError(
            "Solo se puede completar una orden que está en instalación."
        )

    previous_status = work_order.status
    work_order.status = WorkOrder.Status.COMPLETED
    work_order.completed_at = timezone.now()
    work_order.save()

    _create_history(
        work_order=work_order,
        actor=actor,
        event_type=WorkOrderHistory.EventType.COMPLETED,
        description="Orden de trabajo completada.",
        previous_value=previous_status,
        new_value=work_order.status,
    )
    return work_order
