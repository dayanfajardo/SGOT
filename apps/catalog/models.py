from django.db import models


class Product(models.Model):
    """Producto del catálogo: equipo o material."""

    class ProductType(models.TextChoices):
        EQUIPMENT = "EQUIPMENT", "Equipo"
        MATERIAL = "MATERIAL", "Material"

    class Unit(models.TextChoices):
        UNIT = "UNIT", "Unidad"
        METER = "METER", "Metro"
        ROLL = "ROLL", "Rollo"
        BOX = "BOX", "Caja"

    name = models.CharField(
        "nombre",
        max_length=150,
    )
    reference = models.CharField(
        "referencia",
        max_length=80,
        blank=True,
    )
    product_type = models.CharField(
        "tipo de producto",
        max_length=20,
        choices=ProductType.choices,
    )
    unit = models.CharField(
        "unidad",
        max_length=20,
        choices=Unit.choices,
    )
    active = models.BooleanField(
        "activo",
        default=True,
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
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Technician(models.Model):
    """Técnico de planta o contratista."""

    class TechnicianType(models.TextChoices):
        STAFF = "STAFF", "Planta"
        CONTRACTOR = "CONTRACTOR", "Contratista"

    first_name = models.CharField(
        "nombre",
        max_length=100,
    )
    last_name = models.CharField(
        "apellido",
        max_length=100,
        blank=True,
    )
    phone = models.CharField(
        "teléfono",
        max_length=30,
        blank=True,
    )
    technician_type = models.CharField(
        "tipo de técnico",
        max_length=20,
        choices=TechnicianType.choices,
    )
    active = models.BooleanField(
        "activo",
        default=True,
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
        verbose_name = "Técnico"
        verbose_name_plural = "Técnicos"
        ordering = ["first_name", "last_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()


class WorkType(models.Model):
    """Tipo de trabajo que puede realizarse."""

    name = models.CharField(
        "nombre",
        max_length=100,
        unique=True,
    )
    description = models.CharField(
        "descripción",
        max_length=255,
        blank=True,
    )
    active = models.BooleanField(
        "activo",
        default=True,
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
        verbose_name = "Tipo de trabajo"
        verbose_name_plural = "Tipos de trabajo"
        ordering = ["name"]

    def __str__(self):
        return self.name
