from django import forms

from apps.catalog.models import Product, ProductCategory, Technician


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


class ProductFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Buscar producto...",
                "aria-label": "Buscar producto",
            },
        ),
    )
    category = forms.ChoiceField(
        required=False,
        label="",
        choices=[("", "Todas las categorías"), *ProductCategory.choices],
        widget=forms.Select(attrs={"aria-label": "Categoría"}),
    )
    product_type = forms.ChoiceField(
        required=False,
        label="",
        choices=[("", "Todos los tipos"), *Product.ProductType.choices],
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


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "product_code",
            "name",
            "reference",
            "category",
            "product_type",
            "unit",
        )
        labels = {
            "product_code": "Código de producto",
            "name": "Producto",
            "reference": "Referencia / modelo",
            "category": "Categoría",
            "product_type": "Tipo de producto",
            "unit": "Unidad",
        }
        widgets = {
            "product_code": forms.TextInput(),
            "name": forms.TextInput(),
            "reference": forms.TextInput(),
            "category": forms.Select(),
            "product_type": forms.Select(),
            "unit": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].choices = [
            ("", "—"),
            *ProductCategory.choices,
        ]
        if not self.instance.pk:
            self.fields["product_code"].required = True
            self.fields["category"].required = True

    def clean_product_code(self):
        code = (self.cleaned_data.get("product_code") or "").strip()
        return code or None

    def clean_category(self):
        return self.cleaned_data.get("category") or None
