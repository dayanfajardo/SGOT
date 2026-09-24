from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from apps.catalog.models import Product

from .models import WorkOrder, WorkOrderItem

User = get_user_model()


class WorkOrderCreateForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = (
            "number",
            "customer",
            "commercial",
            "work_type",
            "received_date",
            "installation_address",
            "notes",
        )
        labels = {
            "number": "Número",
            "customer": "Cliente",
            "commercial": "Comercial",
            "work_type": "Tipo de trabajo",
            "received_date": "Fecha de recepción",
            "installation_address": "Dirección de instalación",
            "notes": "Notas",
        }
        widgets = {
            "received_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["commercial"].queryset = User.objects.filter(
            is_active=True,
            groups__name="Comercial",
        ).order_by("first_name", "last_name", "username")


class WorkOrderItemForm(forms.ModelForm):
    class Meta:
        model = WorkOrderItem
        fields = (
            "product",
            "requested_quantity",
            "notes",
        )
        labels = {
            "product": "Producto",
            "requested_quantity": "Cantidad solicitada",
            "notes": "Notas",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(
            active=True,
        ).order_by("name")


WorkOrderItemFormSet = inlineformset_factory(
    WorkOrder,
    WorkOrderItem,
    form=WorkOrderItemForm,
    extra=1,
    can_delete=True,
)
