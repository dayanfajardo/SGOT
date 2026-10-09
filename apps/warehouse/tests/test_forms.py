from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.catalog.models import Product, ProductCategory, Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.forms import WarehouseOutputItemForm
from apps.workorders.models import WorkOrder

User = get_user_model()


class WarehouseOutputItemFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="almacen.formularios")
        self.customer = Customer.objects.create(trade_name="Cliente Formulario")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.product = Product.objects.create(
            name="Cable UTP Cat 6 para exteriores",
            product_code="1-5-36",
            reference="ABC123",
            category=ProductCategory.MATERIALS_ACCESSORIES,
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
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
            product_code="2-1-1",
            reference="OLD-99",
            category=ProductCategory.INTRUSION,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
            active=False,
        )
        self.work_order = WorkOrder.objects.create(
            number="9201",
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            status=WorkOrder.Status.EQUIPMENT_OK,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 12),
            created_by=self.user,
        )

    def _item_data(self, **overrides):
        data = {
            "work_order_item": "",
            "product": str(self.product.pk),
            "delivered_quantity": "1",
            "notes": "",
        }
        data.update(overrides)
        return data

    def _form(self, **overrides):
        return WarehouseOutputItemForm(
            data=self._item_data(**overrides),
            work_order=self.work_order,
        )

    def test_delivered_quantity_one_is_valid(self):
        form = self._form(delivered_quantity="1")

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["delivered_quantity"], 1)

    def test_delivered_quantity_larger_integers_are_valid(self):
        form = self._form(delivered_quantity="12")

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["delivered_quantity"], 12)

    def test_delivered_quantity_zero_is_invalid(self):
        form = self._form(delivered_quantity="0")

        self.assertFalse(form.is_valid())
        self.assertIn("delivered_quantity", form.errors)

    def test_delivered_quantity_decimal_is_invalid(self):
        form = self._form(delivered_quantity="1.5")

        self.assertFalse(form.is_valid())
        self.assertIn("delivered_quantity", form.errors)

    def test_integer_quantity_is_compatible_with_decimal_model_field(self):
        form = self._form(delivered_quantity="3")

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            Decimal(form.cleaned_data["delivered_quantity"]),
            Decimal("3"),
        )

    def test_product_queryset_contains_only_active_products(self):
        form = WarehouseOutputItemForm(work_order=self.work_order)
        product_ids = set(
            form.fields["product"].queryset.values_list("pk", flat=True)
        )

        self.assertIn(self.product.pk, product_ids)
        self.assertIn(self.product_without_reference.pk, product_ids)
        self.assertNotIn(self.inactive_product.pk, product_ids)

    def test_product_option_labels_include_code_name_and_reference(self):
        form = WarehouseOutputItemForm(work_order=self.work_order)
        field = form.fields["product"]

        self.assertEqual(
            field.label_from_instance(self.product),
            "1-5-36 · Cable UTP Cat 6 para exteriores · Ref: ABC123",
        )
        self.assertEqual(
            field.label_from_instance(self.product_without_reference),
            "1-1-1 · Cámara IP 4MP",
        )

    def test_product_widget_renders_identifying_option_text(self):
        form = WarehouseOutputItemForm(work_order=self.work_order)
        rendered = str(form["product"])

        self.assertIn("1-5-36 · Cable UTP Cat 6 para exteriores · Ref: ABC123", rendered)
        self.assertIn("1-1-1 · Cámara IP 4MP", rendered)
        self.assertNotIn(self.inactive_product.name, rendered)
        self.assertNotIn("OLD-99", rendered)
