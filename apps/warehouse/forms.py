from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, formset_factory, inlineformset_factory

from apps.catalog.models import Product
from apps.warehouse.models import WarehouseOutput, WarehouseOutputItem
from apps.workorders.models import WorkOrderItem


class WarehouseOutputCreateForm(forms.ModelForm):
    class Meta:
        model = WarehouseOutput
        fields = (
            "number",
            "output_date",
            "notes",
        )
        labels = {
            "number": "Número de salida",
            "output_date": "Fecha de salida",
            "notes": "Notas",
        }
        widgets = {
            "output_date": forms.DateInput(attrs={"type": "date"}),
        }


class WarehouseOutputItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.none(),
        required=False,
        label="Producto / material adicional",
    )

    class Meta:
        model = WarehouseOutputItem
        fields = (
            "work_order_item",
            "product",
            "delivered_quantity",
            "notes",
        )
        labels = {
            "work_order_item": "Ítem de orden de trabajo",
            "product": "Producto / material adicional",
            "delivered_quantity": "Cantidad entregada",
            "notes": "Notas",
        }

    def __init__(self, *args, work_order=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(
            active=True,
        ).order_by("name")

        items = WorkOrderItem.objects.none()
        if work_order is not None:
            items = WorkOrderItem.objects.filter(
                work_order=work_order,
            ).order_by("id")
        self.fields["work_order_item"].queryset = items

    def clean(self):
        cleaned_data = super().clean()
        if self.empty_permitted and not self.has_changed():
            return cleaned_data

        work_order_item = cleaned_data.get("work_order_item")
        product = cleaned_data.get("product")
        if not work_order_item and not product:
            raise ValidationError(
                "Debe seleccionar un ítem de orden de trabajo o un "
                "producto/material adicional."
            )
        return cleaned_data


class BaseWarehouseOutputItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        seen_work_order_items = set()
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            if form.empty_permitted and not form.has_changed():
                continue

            work_order_item = form.cleaned_data.get("work_order_item")
            if work_order_item is None:
                continue

            if work_order_item.pk in seen_work_order_items:
                raise ValidationError(
                    "El mismo ítem de orden de trabajo no puede aparecer "
                    "más de una vez."
                )
            seen_work_order_items.add(work_order_item.pk)


WarehouseOutputItemFormSet = inlineformset_factory(
    WarehouseOutput,
    WarehouseOutputItem,
    form=WarehouseOutputItemForm,
    formset=BaseWarehouseOutputItemFormSet,
    extra=1,
    can_delete=True,
)


class WarehouseReturnItemForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput)
    returned_quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label="Cantidad devuelta",
    )

    def __init__(self, *args, warehouse_output, **kwargs):
        super().__init__(*args, **kwargs)
        self.warehouse_output = warehouse_output

    def clean_item_id(self):
        item_id = self.cleaned_data["item_id"]
        belongs_to_output = WarehouseOutputItem.objects.filter(
            pk=item_id,
            warehouse_output=self.warehouse_output,
        ).exists()
        if not belongs_to_output:
            raise ValidationError(
                "El ítem no pertenece a esta salida de almacén."
            )
        return item_id


WarehouseReturnFormSet = formset_factory(
    WarehouseReturnItemForm,
    extra=0,
    can_delete=False,
)
