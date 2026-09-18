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
        constraints = [
            models.UniqueConstraint(
                fields=["code_system", "customer_code"],
                name="unique_customer_code_per_system",
            ),
        ]

    def __str__(self):
        return self.trade_name
