from django.core.exceptions import ValidationError
from django.db import models


class ProductCategory(models.TextChoices):
    INTRUSION = "INTRUSION", "Intrusión"
    CCTV = "CCTV", "CCTV"
    ELECTRIC_FENCE = "ELECTRIC_FENCE", "Cercas eléctricas"
    ACCESS_CONTROL = "ACCESS_CONTROL", "Control de acceso"
    VEHICULAR = "VEHICULAR", "Línea vehicular"
    MATERIALS_ACCESSORIES = "MATERIALS_ACCESSORIES", "Materiales y accesorios"


PRODUCT_CATEGORY_BY_PREFIX = {
    ("2", "1"): ProductCategory.INTRUSION,
    ("1", "1"): ProductCategory.CCTV,
    ("1", "2"): ProductCategory.ELECTRIC_FENCE,
    ("1", "3"): ProductCategory.ACCESS_CONTROL,
    ("1", "4"): ProductCategory.VEHICULAR,
    ("1", "5"): ProductCategory.MATERIALS_ACCESSORIES,
}

MATERIALS_ACCESSORIES_PREFIX = ("1", "5")


def validate_product_code(*, product_code, category, product_type):
    """Valida formato, prefijo y consistencia del código interno de producto."""
    code = (product_code or "").strip()
    if not code:
        return

    errors = {}
    segments = code.split("-")
    if len(segments) != 3:
        raise ValidationError(
            {
                "product_code": (
                    "El código de producto debe tener exactamente tres "
                    "segmentos separados por guion (ejemplo: 2-1-20)."
                ),
            }
        )

    if not all(segment.isdigit() for segment in segments):
        raise ValidationError(
            {
                "product_code": (
                    "Cada segmento del código de producto debe ser numérico."
                ),
            }
        )

    prefix = (segments[0], segments[1])
    expected_category = PRODUCT_CATEGORY_BY_PREFIX.get(prefix)
    if expected_category is None:
        raise ValidationError(
            {
                "product_code": (
                    "El prefijo del código de producto no corresponde a "
                    "una categoría válida."
                ),
            }
        )

    if category != expected_category:
        errors["category"] = (
            "La categoría no corresponde con el prefijo del código de producto."
        )

    if (
        prefix == MATERIALS_ACCESSORIES_PREFIX
        and product_type != Product.ProductType.MATERIAL
    ):
        errors["product_type"] = (
            "Los productos con código 1-5-* deben ser de tipo material."
        )

    if errors:
        raise ValidationError(errors)


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
    product_code = models.CharField(
        "código de producto",
        max_length=30,
        unique=True,
    )
    reference = models.CharField(
        "referencia / modelo",
        max_length=80,
        blank=True,
    )
    category = models.CharField(
        "categoría",
        max_length=30,
        choices=ProductCategory.choices,
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

    def clean(self):
        super().clean()
        validate_product_code(
            product_code=self.product_code,
            category=self.category,
            product_type=self.product_type,
        )

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
