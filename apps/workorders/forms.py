from django import forms
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory

from apps.catalog.models import Product, Technician

from .models import WorkOrder, WorkOrderItem
from .services import ALLOWED_STATUS_TRANSITIONS

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


class WorkOrderScheduleForm(forms.Form):
    technician = forms.ModelChoiceField(
        queryset=Technician.objects.none(),
        label="Técnico",
    )
    scheduled_date = forms.DateField(
        label="Fecha programada",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, work_order=None, **kwargs):
        if work_order is not None:
            initial = kwargs.setdefault("initial", {})
            if work_order.assigned_technician_id and "technician" not in initial:
                initial["technician"] = work_order.assigned_technician
            if work_order.scheduled_date and "scheduled_date" not in initial:
                initial["scheduled_date"] = work_order.scheduled_date

        super().__init__(*args, **kwargs)
        self.fields["technician"].queryset = Technician.objects.filter(
            active=True,
        ).order_by("first_name", "last_name")


class WorkOrderStatusForm(forms.Form):
    new_status = forms.ChoiceField(
        label="Nuevo estado",
        choices=[],
    )

    def __init__(self, *args, work_order, **kwargs):
        super().__init__(*args, **kwargs)
        allowed = ALLOWED_STATUS_TRANSITIONS.get(work_order.status, set())
        self.fields["new_status"].choices = [
            (value, label)
            for value, label in WorkOrder.Status.choices
            if value in allowed
        ]
