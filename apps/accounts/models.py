from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario personalizado del sistema SGOT.

    Extiende el modelo de usuario proporcionado por Django para permitir
    futuras personalizaciones sin tener que reemplazar el sistema de
    autenticación más adelante.
    """

    email = models.EmailField(
        unique=True,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.get_full_name() or self.username