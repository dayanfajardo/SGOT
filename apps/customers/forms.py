from django import forms

from apps.customers.models import Customer


class CustomerFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar cliente...",
                "aria-label": "Buscar cliente",
            },
        ),
    )
    code_system = forms.ChoiceField(
        required=False,
        label="",
        choices=[("", "Todos los sistemas"), *Customer.CodeSystem.choices],
        widget=forms.Select(attrs={"aria-label": "Sistema"}),
    )


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = (
            "trade_name",
            "legal_name",
            "document",
            "customer_code",
            "code_system",
            "phone",
            "email",
        )
        labels = {
            "trade_name": "Nombre comercial",
            "legal_name": "Razón social",
            "document": "Documento / NIT",
            "customer_code": "Código de cliente",
            "code_system": "Sistema",
            "phone": "Teléfono",
            "email": "Correo electrónico",
        }
        widgets = {
            "trade_name": forms.TextInput(),
            "legal_name": forms.TextInput(),
            "document": forms.TextInput(),
            "customer_code": forms.TextInput(),
            "code_system": forms.Select(),
            "phone": forms.TextInput(),
            "email": forms.EmailInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["code_system"].choices = [
            ("", "—"),
            *Customer.CodeSystem.choices,
        ]

    def clean_customer_code(self):
        return self.cleaned_data.get("customer_code") or None

    def clean_code_system(self):
        return self.cleaned_data.get("code_system") or None
