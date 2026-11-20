from django.test import TestCase

from apps.catalog.models import Product, ProductCategory
from apps.workorders.forms import (
    REQUESTED_QUANTITY_INTEGER_MESSAGE,
    WorkOrderItemForm,
    WorkOrderItemFormSet,
)


class WorkOrderItemFormTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="PANEL CENTRAL 16 ZONAS - SP 6000",
            product_code="2-1-25",
            reference="SP6000",
            category=ProductCategory.INTRUSION,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.product_without_reference = Product.objects.create(
            name="Cámara IP 4MP",
            product_code="1-1-1",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.inactive_product = Product.objects.create(
            name="Sensor inactivo",
            product_code="2-1-99",
            reference="OLD-99",
            category=ProductCategory.INTRUSION,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
            active=False,
        )

    def _form(self, **overrides):
        data = {
            "product": str(self.product.pk),
            "requested_quantity": "1",
            "notes": "",
        }
        data.update(overrides)
        return WorkOrderItemForm(data=data)

    def test_product_queryset_contains_only_active_products(self):
        form = WorkOrderItemForm()
        product_ids = set(
            form.fields["product"].queryset.values_list("pk", flat=True)
        )

        self.assertIn(self.product.pk, product_ids)
        self.assertIn(self.product_without_reference.pk, product_ids)
        self.assertNotIn(self.inactive_product.pk, product_ids)

    def test_product_option_labels_include_code_name_and_reference(self):
        form = WorkOrderItemForm()
        field = form.fields["product"]

        self.assertEqual(
            field.label_from_instance(self.product),
            "2-1-25 · PANEL CENTRAL 16 ZONAS - SP 6000 · Ref: SP6000",
        )
        self.assertEqual(
            field.label_from_instance(self.product_without_reference),
            "1-1-1 · Cámara IP 4MP",
        )

    def test_product_widget_renders_identifying_option_text(self):
        form = WorkOrderItemForm()
        rendered = str(form["product"])

        self.assertIn(
            "2-1-25 · PANEL CENTRAL 16 ZONAS - SP 6000 · Ref: SP6000",
            rendered,
        )
        self.assertIn("1-1-1 · Cámara IP 4MP", rendered)
        self.assertNotIn(self.inactive_product.name, rendered)
        self.assertNotIn("OLD-99", rendered)

    def test_requested_quantity_one_is_valid(self):
        form = self._form(requested_quantity="1")

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["requested_quantity"], 1)

    def test_requested_quantity_five_is_valid(self):
        form = self._form(requested_quantity="5")

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["requested_quantity"], 5)

    def test_requested_quantity_zero_is_invalid(self):
        form = self._form(requested_quantity="0")

        self.assertFalse(form.is_valid())
        self.assertIn("requested_quantity", form.errors)
        self.assertIn(
            REQUESTED_QUANTITY_INTEGER_MESSAGE,
            form.errors["requested_quantity"],
        )

    def test_requested_quantity_negative_is_invalid(self):
        form = self._form(requested_quantity="-1")

        self.assertFalse(form.is_valid())
        self.assertIn("requested_quantity", form.errors)
        self.assertIn(
            REQUESTED_QUANTITY_INTEGER_MESSAGE,
            form.errors["requested_quantity"],
        )

    def test_requested_quantity_decimal_one_point_five_is_invalid(self):
        form = self._form(requested_quantity="1.5")

        self.assertFalse(form.is_valid())
        self.assertIn("requested_quantity", form.errors)
        self.assertIn(
            REQUESTED_QUANTITY_INTEGER_MESSAGE,
            form.errors["requested_quantity"],
        )

    def test_requested_quantity_decimal_zero_point_zero_one_is_invalid(self):
        form = self._form(requested_quantity="0.01")

        self.assertFalse(form.is_valid())
        self.assertIn("requested_quantity", form.errors)
        self.assertIn(
            REQUESTED_QUANTITY_INTEGER_MESSAGE,
            form.errors["requested_quantity"],
        )

    def test_requested_quantity_widget_uses_integer_step(self):
        form = WorkOrderItemForm()
        rendered = str(form["requested_quantity"])

        self.assertIn('min="1"', rendered)
        self.assertIn('step="1"', rendered)

    def test_formset_accepts_multiple_valid_items(self):
        formset = WorkOrderItemFormSet(
            data={
                "items-TOTAL_FORMS": "2",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-product": str(self.product.pk),
                "items-0-requested_quantity": "2",
                "items-0-notes": "",
                "items-1-product": str(self.product_without_reference.pk),
                "items-1-requested_quantity": "5",
                "items-1-notes": "Cable",
            }
        )

        self.assertTrue(formset.is_valid(), formset.errors)
        cleaned_items = [
            form.cleaned_data
            for form in formset
            if form.cleaned_data and not form.cleaned_data.get("DELETE")
        ]
        self.assertEqual(len(cleaned_items), 2)
        self.assertEqual(cleaned_items[0]["product"], self.product)
        self.assertEqual(cleaned_items[0]["requested_quantity"], 2)
        self.assertEqual(
            cleaned_items[1]["product"],
            self.product_without_reference,
        )
        self.assertEqual(cleaned_items[1]["requested_quantity"], 5)

    def test_formset_rejects_decimal_requested_quantity(self):
        formset = WorkOrderItemFormSet(
            data={
                "items-TOTAL_FORMS": "1",
                "items-INITIAL_FORMS": "0",
                "items-MIN_NUM_FORMS": "0",
                "items-MAX_NUM_FORMS": "1000",
                "items-0-product": str(self.product.pk),
                "items-0-requested_quantity": "1.5",
                "items-0-notes": "",
            }
        )

        self.assertFalse(formset.is_valid())
        self.assertIn("requested_quantity", formset.forms[0].errors)
