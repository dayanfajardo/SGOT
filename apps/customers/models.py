from django.db import models


class Customer(models.Model):
    """Cliente de la empresa de seguridad electrónica."""

    class CodeSystem(models.TextChoices):
        CENTURION = "CENTURION", "Centurión"
        ARION = "ARION", "Arion"

    customer_code = models.CharField(
        "código de cliente",
        max_length=20,
        blank=True,
        null=True,
        unique=True,
    )
    code_system = models.CharField(
        "sistema de código",
        max_length=20,
        choices=CodeSystem.choices,
        blank=True,
        null=True,
    )
    trade_name = models.CharField(
        "nombre comercial",
        max_length=150,
    )
    legal_name = models.CharField(
        "razón social",
        max_length=150,
        blank=True,
    )
    document = models.CharField(
        "documento o NIT",
        max_length=30,
        blank=True,
    )
    phone = models.CharField(
        "teléfono",
        max_length=30,
        blank=True,
    )
    email = models.EmailField(
        "correo electrónico",
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
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["trade_name"]

    def __str__(self):
        code = (self.customer_code or "").strip()
        if code:
            return f"{self.trade_name} - {code}"
        return self.trade_name
