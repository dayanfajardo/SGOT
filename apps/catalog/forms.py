from django import forms

from apps.catalog.models import Technician


class TechnicianFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar técnico...",
                "aria-label": "Buscar técnico",
            },
        ),
    )
    technician_type = forms.ChoiceField(
        required=False,
        label="",
        choices=[("", "Todos los tipos"), *Technician.TechnicianType.choices],
        widget=forms.Select(attrs={"aria-label": "Tipo"}),
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


class TechnicianForm(forms.ModelForm):
    class Meta:
        model = Technician
        fields = (
            "first_name",
            "last_name",
            "phone",
            "technician_type",
        )
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "phone": "Teléfono",
            "technician_type": "Tipo de técnico",
        }
        widgets = {
            "first_name": forms.TextInput(),
            "last_name": forms.TextInput(),
            "phone": forms.TextInput(),
            "technician_type": forms.Select(),
        }
