from django.conf import settings
from django.db import models


class WarehouseOutput(models.Model):
    """Salida física de almacén asociada a una orden de trabajo."""

    number = models.CharField(
        "número",
        max_length=20,
        unique=True,
    )
    work_order = models.OneToOneField(
        "workorders.WorkOrder",
        on_delete=models.PROTECT,
        related_name="warehouse_output",
        verbose_name="orden de trabajo",
    )
    technician = models.ForeignKey(
        "catalog.Technician",
        on_delete=models.PROTECT,
        related_name="warehouse_outputs",
        verbose_name="técnico",
    )
    output_date = models.DateField(
        "fecha de salida",
    )
    notes = models.TextField(
        "notas",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_warehouse_outputs",
        verbose_name="creado por",
    )
    created_at = models.DateTimeField(
        "fecha de creación",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "fecha de actualización",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Salida de almacén"
        verbose_name_plural = "Salidas de almacén"
        ordering = ["-output_date", "-id"]

    def __str__(self):
        return f"Salida {self.number} - OT {self.work_order.number}"


class WarehouseOutputItem(models.Model):
    """Producto entregado en una salida de almacén."""

    warehouse_output = models.ForeignKey(
        WarehouseOutput,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="salida de almacén",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="warehouse_output_items",
        verbose_name="producto",
    )
    work_order_item = models.ForeignKey(
        "workorders.WorkOrderItem",
        on_delete=models.PROTECT,
        related_name="warehouse_output_items",
        verbose_name="ítem de orden de trabajo",
        blank=True,
        null=True,
    )
    delivered_quantity = models.DecimalField(
        "cantidad entregada",
        max_digits=10,
        decimal_places=2,
    )
    returned_quantity = models.DecimalField(
        "cantidad devuelta",
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    notes = models.CharField(
        "notas",
        max_length=255,
        blank=True,
    )
    created_at = models.DateTimeField(
        "fecha de creación",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "fecha de actualización",
        auto_now=True,
    )

    class Meta:
        verbose_name = "Ítem de salida de almacén"
        verbose_name_plural = "Ítems de salidas de almacén"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(delivered_quantity__gt=0),
                name="warehouseoutputitem_delivered_quantity_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(returned_quantity__gte=0),
                name="warehouseoutputitem_returned_quantity_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    returned_quantity__lte=models.F("delivered_quantity"),
                ),
                name="warehouseoutputitem_returned_quantity_lte_delivered",
            ),
        ]

    def __str__(self):
        return (
            f"Salida {self.warehouse_output.number} - "
            f"{self.product} x {self.delivered_quantity}"
        )

    @property
    def used_quantity(self):
        return self.delivered_quantity - self.returned_quantity
