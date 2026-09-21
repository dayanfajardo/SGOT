from django.conf import settings
from django.db import models


class WorkOrder(models.Model):
    """Orden de trabajo de instalación o servicio."""

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Recibida"
        PENDING_EQUIPMENT = "PENDING_EQUIPMENT", "Pdte. llegada de equipos"
        EQUIPMENT_OK = "EQUIPMENT_OK", "Equipos OK"
        IN_INSTALLATION = "IN_INSTALLATION", "En instalación"
        COMPLETED = "COMPLETED", "Completada"

    number = models.CharField(
        "número",
        max_length=20,
        unique=True,
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="cliente",
    )
    commercial = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="commercial_work_orders",
        verbose_name="comercial",
    )
    work_type = models.ForeignKey(
        "catalog.WorkType",
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="tipo de trabajo",
    )
    status = models.CharField(
        "estado",
        max_length=32,
        choices=Status.choices,
        default=Status.RECEIVED,
    )
    assigned_technician = models.ForeignKey(
        "catalog.Technician",
        on_delete=models.PROTECT,
        related_name="work_orders",
        verbose_name="técnico asignado",
        blank=True,
        null=True,
    )
    received_date = models.DateField(
        "fecha de recepción",
    )
    scheduled_date = models.DateField(
        "fecha programada",
        blank=True,
        null=True,
    )
    installation_started_at = models.DateTimeField(
        "inicio de instalación",
        blank=True,
        null=True,
    )
    completed_at = models.DateTimeField(
        "fecha de finalización",
        blank=True,
        null=True,
    )
    installation_address = models.CharField(
        "dirección de instalación",
        max_length=255,
        blank=True,
    )
    notes = models.TextField(
        "notas",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_work_orders",
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
        verbose_name = "Orden de trabajo"
        verbose_name_plural = "Órdenes de trabajo"
        ordering = ["-received_date", "-id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["received_date"]),
            models.Index(fields=["scheduled_date"]),
        ]

    def __str__(self):
        return f"OT {self.number} - {self.customer}"


class WorkOrderItem(models.Model):
    """Ítem de producto solicitado en una orden de trabajo."""

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="orden de trabajo",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.PROTECT,
        related_name="work_order_items",
        verbose_name="producto",
    )
    requested_quantity = models.DecimalField(
        "cantidad solicitada",
        max_digits=10,
        decimal_places=2,
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

    class Meta:
        verbose_name = "Ítem de orden de trabajo"
        verbose_name_plural = "Ítems de órdenes de trabajo"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(requested_quantity__gt=0),
                name="workorderitem_requested_quantity_positive",
            ),
        ]

    def __str__(self):
        return f"OT {self.work_order.number} - {self.product} x {self.requested_quantity}"


class WorkOrderHistory(models.Model):
    """Registro de eventos de una orden de trabajo."""

    class EventType(models.TextChoices):
        CREATED = "CREATED", "Creación"
        UPDATED = "UPDATED", "Actualización"
        STATUS_CHANGED = "STATUS_CHANGED", "Cambio de estado"
        SCHEDULED = "SCHEDULED", "Programación"
        RESCHEDULED = "RESCHEDULED", "Reprogramación"
        TECHNICIAN_CHANGED = "TECHNICIAN_CHANGED", "Cambio de técnico"
        INSTALLATION_STARTED = "INSTALLATION_STARTED", "Inicio de instalación"
        COMPLETED = "COMPLETED", "Finalización"

    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name="history",
        verbose_name="orden de trabajo",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="work_order_history_entries",
        verbose_name="usuario",
    )
    event_type = models.CharField(
        "tipo de evento",
        max_length=32,
        choices=EventType.choices,
    )
    description = models.TextField(
        "descripción",
    )
    previous_value = models.TextField(
        "valor anterior",
        blank=True,
    )
    new_value = models.TextField(
        "valor nuevo",
        blank=True,
    )
    created_at = models.DateTimeField(
        "fecha de creación",
        auto_now_add=True,
    )

    class Meta:
        verbose_name = "Historial de orden"
        verbose_name_plural = "Historial de órdenes"
        ordering = ["-created_at"]
