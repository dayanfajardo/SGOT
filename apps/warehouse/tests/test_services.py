from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalog.models import Product, Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.models import WarehouseOutput, WarehouseOutputItem
from apps.warehouse.services import (
    add_output_item,
    create_warehouse_output,
    update_returned_quantity,
)
from apps.workorders.models import WorkOrder, WorkOrderItem

User = get_user_model()


class CreateWarehouseOutputServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="almacen.servicios")
        self.customer = Customer.objects.create(trade_name="Alarmas del Norte")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.other_technician = Technician.objects.create(
            first_name="Ana",
            last_name="Gómez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.inactive_technician = Technician.objects.create(
            first_name="Luis",
            last_name="Rojas",
            technician_type=Technician.TechnicianType.CONTRACTOR,
            active=False,
        )

    def _create_work_order(self, **kwargs):
        data = {
            "number": "8072",
            "customer": self.customer,
            "commercial": self.user,
            "work_type": self.work_type,
            "status": WorkOrder.Status.EQUIPMENT_OK,
            "assigned_technician": self.technician,
            "received_date": date(2026, 9, 10),
            "created_by": self.user,
        }
        data.update(kwargs)
        return WorkOrder.objects.create(**data)

    def test_create_output_for_equipment_ok_order(self):
        work_order = self._create_work_order()

        output = create_warehouse_output(
            number="5256",
            work_order=work_order,
            technician=self.technician,
            output_date=date(2026, 9, 18),
            created_by=self.user,
            notes="Entrega de equipos.",
        )
        output.refresh_from_db()

        self.assertEqual(output.number, "5256")
        self.assertEqual(output.work_order, work_order)
        self.assertEqual(output.technician, self.technician)
        self.assertEqual(output.output_date, date(2026, 9, 18))
        self.assertEqual(output.created_by, self.user)
        self.assertEqual(output.notes, "Entrega de equipos.")

    def test_rejects_order_that_is_not_equipment_ok(self):
        work_order = self._create_work_order(status=WorkOrder.Status.RECEIVED)

        with self.assertRaises(ValidationError):
            create_warehouse_output(
                number="5256",
                work_order=work_order,
                technician=self.technician,
                output_date=date(2026, 9, 18),
                created_by=self.user,
            )

    def test_rejects_order_without_assigned_technician(self):
        work_order = self._create_work_order(assigned_technician=None)

        with self.assertRaises(ValidationError):
            create_warehouse_output(
                number="5256",
                work_order=work_order,
                technician=self.technician,
                output_date=date(2026, 9, 18),
                created_by=self.user,
            )

    def test_rejects_missing_technician(self):
        work_order = self._create_work_order()

        with self.assertRaises(ValidationError):
            create_warehouse_output(
                number="5256",
                work_order=work_order,
                technician=None,
                output_date=date(2026, 9, 18),
                created_by=self.user,
            )

    def test_rejects_technician_different_from_assigned(self):
        work_order = self._create_work_order()

        with self.assertRaises(ValidationError):
            create_warehouse_output(
                number="5256",
                work_order=work_order,
                technician=self.other_technician,
                output_date=date(2026, 9, 18),
                created_by=self.user,
            )

    def test_rejects_inactive_technician(self):
        work_order = self._create_work_order(
            assigned_technician=self.inactive_technician,
        )

        with self.assertRaises(ValidationError):
            create_warehouse_output(
                number="5256",
                work_order=work_order,
                technician=self.inactive_technician,
                output_date=date(2026, 9, 18),
                created_by=self.user,
            )

    def test_rejects_second_output_for_same_order(self):
        work_order = self._create_work_order()
        create_warehouse_output(
            number="5256",
            work_order=work_order,
            technician=self.technician,
            output_date=date(2026, 9, 18),
            created_by=self.user,
        )

        with self.assertRaises(ValidationError):
            create_warehouse_output(
                number="5257",
                work_order=work_order,
                technician=self.technician,
                output_date=date(2026, 9, 19),
                created_by=self.user,
            )

        self.assertEqual(WarehouseOutput.objects.filter(work_order=work_order).count(), 1)


class AddOutputItemServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="almacen.items.servicios")
        self.customer = Customer.objects.create(trade_name="Seguridad Andina")
        self.work_type = WorkType.objects.create(name="Mantenimiento")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.work_order = WorkOrder.objects.create(
            number="9101",
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            status=WorkOrder.Status.EQUIPMENT_OK,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 12),
            created_by=self.user,
        )
        self.product = Product.objects.create(
            name="Cámara IP 4MP",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.output = create_warehouse_output(
            number="5256",
            work_order=self.work_order,
            technician=self.technician,
            output_date=date(2026, 9, 18),
            created_by=self.user,
        )

    def test_add_product_to_output(self):
        item = add_output_item(
            warehouse_output=self.output,
            product=self.product,
            delivered_quantity=Decimal("2.00"),
            notes="Equipo principal.",
        )
        item.refresh_from_db()

        self.assertEqual(item.warehouse_output, self.output)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.delivered_quantity, Decimal("2.00"))
        self.assertEqual(item.notes, "Equipo principal.")
        self.assertEqual(item.returned_quantity, Decimal("0"))

    def test_link_work_order_item_from_same_order(self):
        work_order_item = WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("2.00"),
        )

        item = add_output_item(
            warehouse_output=self.output,
            product=self.product,
            delivered_quantity=Decimal("2.00"),
            work_order_item=work_order_item,
        )
        item.refresh_from_db()

        self.assertEqual(item.work_order_item, work_order_item)

    def test_allows_additional_material_without_work_order_item(self):
        item = add_output_item(
            warehouse_output=self.output,
            product=self.product,
            delivered_quantity=Decimal("5.00"),
            work_order_item=None,
        )
        item.refresh_from_db()

        self.assertIsNone(item.work_order_item)

    def test_rejects_zero_delivered_quantity(self):
        with self.assertRaises(ValidationError):
            add_output_item(
                warehouse_output=self.output,
                product=self.product,
                delivered_quantity=Decimal("0.00"),
            )

        self.assertEqual(WarehouseOutputItem.objects.count(), 0)

    def test_rejects_negative_delivered_quantity(self):
        with self.assertRaises(ValidationError):
            add_output_item(
                warehouse_output=self.output,
                product=self.product,
                delivered_quantity=Decimal("-1.00"),
            )

    def test_rejects_work_order_item_from_another_order(self):
        other_order = WorkOrder.objects.create(
            number="9102",
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            status=WorkOrder.Status.EQUIPMENT_OK,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 12),
            created_by=self.user,
        )
        other_item = WorkOrderItem.objects.create(
            work_order=other_order,
            product=self.product,
            requested_quantity=Decimal("1.00"),
        )

        with self.assertRaises(ValidationError):
            add_output_item(
                warehouse_output=self.output,
                product=self.product,
                delivered_quantity=Decimal("1.00"),
                work_order_item=other_item,
            )

    def test_rejects_product_that_does_not_match_work_order_item(self):
        other_product = Product.objects.create(
            name="Cable UTP Cat6",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )
        work_order_item = WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("2.00"),
        )

        with self.assertRaises(ValidationError):
            add_output_item(
                warehouse_output=self.output,
                product=other_product,
                delivered_quantity=Decimal("1.00"),
                work_order_item=work_order_item,
            )


class UpdateReturnedQuantityServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="almacen.devolucion")
        self.customer = Customer.objects.create(trade_name="Norte Electrónica")
        self.work_type = WorkType.objects.create(name="Soporte técnico")
        self.technician = Technician.objects.create(
            first_name="Ana",
            last_name="Gómez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.work_order = WorkOrder.objects.create(
            number="9202",
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            status=WorkOrder.Status.EQUIPMENT_OK,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 14),
            created_by=self.user,
        )
        self.product = Product.objects.create(
            name="Sensor PIR",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.output = create_warehouse_output(
            number="5300",
            work_order=self.work_order,
            technician=self.technician,
            output_date=date(2026, 9, 20),
            created_by=self.user,
        )
        self.item = add_output_item(
            warehouse_output=self.output,
            product=self.product,
            delivered_quantity=Decimal("4.00"),
        )

    def test_update_valid_returned_quantity(self):
        update_returned_quantity(
            output_item=self.item,
            returned_quantity=Decimal("1.50"),
        )
        self.item.refresh_from_db()

        self.assertEqual(self.item.returned_quantity, Decimal("1.50"))
        self.assertEqual(self.item.used_quantity, Decimal("2.50"))

    def test_rejects_negative_returned_quantity(self):
        with self.assertRaises(ValidationError):
            update_returned_quantity(
                output_item=self.item,
                returned_quantity=Decimal("-1.00"),
            )

        self.item.refresh_from_db()
        self.assertEqual(self.item.returned_quantity, Decimal("0"))

    def test_rejects_returned_quantity_greater_than_delivered(self):
        with self.assertRaises(ValidationError):
            update_returned_quantity(
                output_item=self.item,
                returned_quantity=Decimal("5.00"),
            )

        self.item.refresh_from_db()
        self.assertEqual(self.item.returned_quantity, Decimal("0"))

    def test_allows_returning_the_full_delivered_quantity(self):
        update_returned_quantity(
            output_item=self.item,
            returned_quantity=Decimal("4.00"),
        )
        self.item.refresh_from_db()

        self.assertEqual(self.item.returned_quantity, Decimal("4.00"))
        self.assertEqual(self.item.used_quantity, Decimal("0.00"))
