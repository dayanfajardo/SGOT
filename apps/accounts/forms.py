from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import transaction

from apps.accounts.constants import ADMIN_GROUP, DEFAULT_GROUPS

User = get_user_model()

ROLE_CHOICES = [
    ("", "Todos los roles"),
    *[(name, name) for name in DEFAULT_GROUPS],
]

ASSIGNABLE_ROLE_CHOICES = [(name, name) for name in DEFAULT_GROUPS]

USERNAME_FORMAT_VALIDATOR = RegexValidator(
    regex=r"^[a-z0-9._-]+$",
    message=(
        "El username solo puede contener letras, números, punto, guion y guion bajo."
    ),
)


def _normalize_email(email):
    if email:
        return email.strip().lower() or None
    return None


def _current_assignable_role(user):
    group_names = set(user.groups.values_list("name", flat=True))
    for name in DEFAULT_GROUPS:
        if name in group_names:
            return name
    return ""


class NormalizedUsernameField(forms.CharField):
    def to_python(self, value):
        value = super().to_python(value)
        if value in self.empty_values:
            return ""
        return str(value).strip().lower()


class UserFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar usuario...",
                "aria-label": "Buscar usuario",
            },
        ),
    )
    role = forms.ChoiceField(
        required=False,
        label="",
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"aria-label": "Rol"}),
    )
    active = forms.ChoiceField(
        required=False,
        label="",
        choices=[
            ("", "Todos"),
            ("1", "Activos"),
            ("0", "Inactivos"),
        ],
        widget=forms.Select(attrs={"aria-label": "Estado"}),
    )


class UserCreateForm(UserCreationForm):
    role = forms.ChoiceField(
        label="Rol",
        choices=ASSIGNABLE_ROLE_CHOICES,
        widget=forms.Select(),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Username",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo",
        }
        widgets = {
            "username": forms.TextInput(),
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "email": forms.EmailInput(),
        }
        error_messages = {
            "username": {
                "unique": "Ya existe un usuario con este username.",
            },
            "email": {
                "unique": "Ya existe un usuario con este correo.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("usable_password", None)
        self.fields["password1"].label = "Contraseña inicial"
        self.fields["password2"].label = "Confirmar contraseña"
        self.order_fields(
            [
                "username",
                "first_name",
                "last_name",
                "email",
                "role",
                "password1",
                "password2",
            ]
        )

    def clean_email(self):
        return _normalize_email(self.cleaned_data.get("email"))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        if not user.email:
            user.email = None
        if commit:
            with transaction.atomic():
                user.save()
                group = Group.objects.get(name=self.cleaned_data["role"])
                user.groups.set([group])
        return user


class UserUpdateForm(forms.ModelForm):
    username = NormalizedUsernameField(
        label="Username",
        max_length=150,
        validators=[UnicodeUsernameValidator(), USERNAME_FORMAT_VALIDATOR],
        widget=forms.TextInput(),
        help_text="Cambiar el username modifica el identificador usado para iniciar sesión.",
        error_messages={
            "unique": "Ya existe un usuario con este username.",
        },
    )
    role = forms.ChoiceField(
        label="Rol",
        choices=ASSIGNABLE_ROLE_CHOICES,
        widget=forms.Select(),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {
            "username": "Username",
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo",
        }
        widgets = {
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "email": forms.EmailInput(),
        }
        error_messages = {
            "username": {
                "unique": "Ya existe un usuario con este username.",
            },
            "email": {
                "unique": "Ya existe un usuario con este correo.",
            },
        }

    def __init__(self, *args, requesting_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.requesting_user = requesting_user
        current_role = _current_assignable_role(self.instance)
        if current_role:
            self.initial.setdefault("role", current_role)
        self.order_fields(
            ["username", "first_name", "last_name", "email", "role"]
        )

    def clean_email(self):
        return _normalize_email(self.cleaned_data.get("email"))

    def clean_username(self):
        username = self.cleaned_data.get("username") or ""
        if " " in username:
            raise forms.ValidationError("El username no puede contener espacios.")
        qs = User.objects.filter(username__iexact=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un usuario con este username.")
        return username

    def clean_role(self):
        role = self.cleaned_data.get("role")
        requesting_user = self.requesting_user
        if (
            requesting_user is not None
            and self.instance.pk
            and requesting_user.pk == self.instance.pk
            and requesting_user.groups.filter(name=ADMIN_GROUP).exists()
            and role != ADMIN_GROUP
        ):
            raise forms.ValidationError(
                "No puedes quitarte tu propio rol de Administrador."
            )
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.email:
            user.email = None
        if commit:
            with transaction.atomic():
                user.save()
                group = Group.objects.get(name=self.cleaned_data["role"])
                user.groups.set([group])
        return user


class UserResetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("usable_password", None)
