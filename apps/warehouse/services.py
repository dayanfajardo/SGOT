from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.warehouse.models import WarehouseOutput, WarehouseOutputItem
from apps.workorders.models import WorkOrder


@transaction.atomic
def create_warehouse_output(
    *,
    number,
    work_order,
    technician,
    output_date,
    created_by,
    notes="",
):
    if work_order.status != WorkOrder.Status.EQUIPMENT_OK:
        raise ValidationError(
            "Solo se puede crear una salida de almacén si la orden cumple con todos los equipos requeridos."
        )

    if work_order.assigned_technician_id is None:
        raise ValidationError("La orden debe tener un técnico asignado.")

    if technician is None:
        raise ValidationError("Se debe seleccionar un técnico.")

    if work_order.assigned_technician_id != technician.pk:
        raise ValidationError(
            "El técnico de la salida debe ser el técnico asignado a la orden."
        )

    if not technician.active:
        raise ValidationError("El técnico debe estar activo.")

    if WarehouseOutput.objects.filter(work_order=work_order).exists():
        raise ValidationError("La orden ya tiene una salida de almacén.")

    return WarehouseOutput.objects.create(
        number=number,
        work_order=work_order,
        technician=technician,
        output_date=output_date,
        created_by=created_by,
        notes=notes,
    )


@transaction.atomic
def add_output_item(
    *,
    warehouse_output,
    product,
    delivered_quantity,
    work_order_item=None,
    notes="",
):
    if delivered_quantity <= 0:
        raise ValidationError("La cantidad entregada debe ser mayor que cero.")

    if work_order_item is not None:
        if work_order_item.work_order_id != warehouse_output.work_order_id:
            raise ValidationError(
                "El ítem debe pertenecer a la misma orden de trabajo de la salida."
            )

        if work_order_item.product_id != product.pk:
            raise ValidationError(
                "El producto debe coincidir con el producto del ítem de la orden."
            )

    return WarehouseOutputItem.objects.create(
        warehouse_output=warehouse_output,
        product=product,
        work_order_item=work_order_item,
        delivered_quantity=delivered_quantity,
        notes=notes,
    )


@transaction.atomic
def update_returned_quantity(*, output_item, returned_quantity):
    if returned_quantity < 0:
        raise ValidationError("La cantidad devuelta no puede ser negativa.")

    if returned_quantity > output_item.delivered_quantity:
        raise ValidationError(
            "La cantidad devuelta no puede ser mayor que la cantidad entregada."
        )

    output_item.returned_quantity = returned_quantity
    output_item.save()
    return output_item


@transaction.atomic
def reconcile_warehouse_output(*, warehouse_output, actor):
    if warehouse_output.reconciled_at is not None:
        raise ValidationError("La salida de almacén ya está conciliada.")

    work_order = warehouse_output.work_order
    if work_order.status != WorkOrder.Status.IN_INSTALLATION:
        raise ValidationError(
            "Solo se puede conciliar una salida si la orden está en instalación."
        )

    warehouse_output.reconciled_at = timezone.now()
    warehouse_output.reconciled_by = actor
    warehouse_output.save()
    return warehouse_output
