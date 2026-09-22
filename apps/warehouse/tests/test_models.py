from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.catalog.models import Product, Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.models import WarehouseOutput, WarehouseOutputItem
from apps.workorders.models import WorkOrder, WorkOrderItem

User = get_user_model()


class WarehouseOutputModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="almacen.salida")
        self.customer = Customer.objects.create(trade_name="Alarmas del Norte")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.work_order = self._create_work_order()

    def _create_work_order(self, **kwargs):
        data = {
            "number": "8072",
            "customer": self.customer,
            "commercial": self.user,
            "work_type": self.work_type,
            "received_date": date(2026, 9, 10),
            "created_by": self.user,
        }
        data.update(kwargs)
        return WorkOrder.objects.create(**data)

    def _create_output(self, **kwargs):
        data = {
            "number": "5256",
            "work_order": self.work_order,
            "technician": self.technician,
            "output_date": date(2026, 9, 18),
            "created_by": self.user,
        }
        data.update(kwargs)
        return WarehouseOutput.objects.create(**data)

    def test_create_warehouse_output(self):
        output = self._create_output()

        self.assertIsNotNone(output.pk)
        self.assertEqual(output.number, "5256")
        self.assertEqual(output.work_order, self.work_order)
        self.assertEqual(output.technician, self.technician)
        self.assertEqual(output.output_date, date(2026, 9, 18))
        self.assertEqual(output.created_by, self.user)

    def test_str_includes_output_and_work_order_numbers(self):
        output = self._create_output()

        self.assertEqual(str(output), "Salida 5256 - OT 8072")

    def test_number_is_unique(self):
        self._create_output(number="5256")
        other_order = self._create_work_order(number="8073")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_output(number="5256", work_order=other_order)

    def test_work_order_can_have_only_one_output(self):
        self._create_output(number="5256")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_output(number="5257")

    def test_ordering_by_output_date_and_id_descending(self):
        older = self._create_output(
            number="2001",
            work_order=self._create_work_order(number="1001"),
            output_date=date(2026, 9, 1),
        )
        newer_first = self._create_output(
            number="2002",
            work_order=self._create_work_order(number="1002"),
            output_date=date(2026, 9, 20),
        )
        newer_second = self._create_output(
            number="2003",
            work_order=self._create_work_order(number="1003"),
            output_date=date(2026, 9, 20),
        )

        outputs = list(WarehouseOutput.objects.all())

        self.assertEqual(outputs, [newer_second, newer_first, older])


class WarehouseOutputItemModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="almacen.items")
        self.customer = Customer.objects.create(trade_name="Seguridad Andina")
        self.work_type = WorkType.objects.create(name="Mantenimiento")
        self.technician = Technician.objects.create(
            first_name="Ana",
            last_name="Gómez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.work_order = WorkOrder.objects.create(
            number="9101",
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            received_date=date(2026, 9, 12),
            created_by=self.user,
        )
        self.product = Product.objects.create(
            name="Cámara IP 4MP",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.output = WarehouseOutput.objects.create(
            number="5256",
            work_order=self.work_order,
            technician=self.technician,
            output_date=date(2026, 9, 18),
            created_by=self.user,
        )

    def _create_item(self, **kwargs):
        data = {
            "warehouse_output": self.output,
            "product": self.product,
            "delivered_quantity": Decimal("2.00"),
        }
        data.update(kwargs)
        return WarehouseOutputItem.objects.create(**data)

    def test_create_item_for_output_and_product(self):
        item = self._create_item(delivered_quantity=Decimal("2.00"))

        self.assertIsNotNone(item.pk)
        self.assertEqual(item.warehouse_output, self.output)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.delivered_quantity, Decimal("2.00"))

    def test_item_can_be_linked_to_work_order_item(self):
        work_order_item = WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("2.00"),
        )
        item = self._create_item(work_order_item=work_order_item)

        self.assertEqual(item.work_order_item, work_order_item)

    def test_item_can_exist_without_work_order_item(self):
        item = self._create_item(work_order_item=None)

        self.assertIsNone(item.work_order_item)

    def test_used_quantity_is_delivered_minus_returned(self):
        item = self._create_item(
            delivered_quantity=Decimal("5.00"),
            returned_quantity=Decimal("2.00"),
        )

        self.assertEqual(item.used_quantity, Decimal("3.00"))

    def test_returned_quantity_defaults_to_zero(self):
        item = self._create_item()

        self.assertEqual(item.returned_quantity, Decimal("0"))

    def test_delivered_quantity_cannot_be_zero(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_item(delivered_quantity=Decimal("0.00"))

    def test_delivered_quantity_cannot_be_negative(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_item(delivered_quantity=Decimal("-1.00"))

    def test_returned_quantity_cannot_be_negative(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_item(returned_quantity=Decimal("-1.00"))

    def test_returned_quantity_cannot_exceed_delivered_quantity(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_item(
                    delivered_quantity=Decimal("2.00"),
                    returned_quantity=Decimal("3.00"),
                )

    def test_str_identifies_output_product_and_delivered_quantity(self):
        item = self._create_item(delivered_quantity=Decimal("3.50"))

        self.assertEqual(str(item), "Salida 5256 - Cámara IP 4MP x 3.50")
