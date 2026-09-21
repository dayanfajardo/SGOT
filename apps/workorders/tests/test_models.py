from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Product, Technician, WorkType
from apps.customers.models import Customer
from apps.workorders.models import WorkOrder, WorkOrderHistory, WorkOrderItem

User = get_user_model()


class WorkOrderModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="comercial.ot")
        self.customer = Customer.objects.create(trade_name="Alarmas del Norte")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")

    def _create_work_order(self, **kwargs):
        data = {
            "number": "8042",
            "customer": self.customer,
            "commercial": self.user,
            "work_type": self.work_type,
            "received_date": date(2026, 9, 10),
            "created_by": self.user,
        }
        data.update(kwargs)
        return WorkOrder.objects.create(**data)

    def test_create_work_order(self):
        technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        work_order = self._create_work_order(
            assigned_technician=technician,
            scheduled_date=date(2026, 9, 15),
        )

        self.assertIsNotNone(work_order.pk)
        self.assertEqual(work_order.number, "8042")
        self.assertEqual(work_order.customer, self.customer)
        self.assertEqual(work_order.work_type, self.work_type)
        self.assertEqual(work_order.assigned_technician, technician)

    def test_default_status_is_received(self):
        work_order = self._create_work_order()

        self.assertEqual(work_order.status, WorkOrder.Status.RECEIVED)

    def test_str_includes_number_and_customer(self):
        work_order = self._create_work_order(number="8042")

        self.assertEqual(str(work_order), "OT 8042 - Alarmas del Norte")

    def test_number_is_unique(self):
        self._create_work_order(number="8042")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_work_order(number="8042")

    def test_work_order_can_exist_without_technician_or_scheduled_date(self):
        work_order = self._create_work_order()

        self.assertIsNone(work_order.assigned_technician)
        self.assertIsNone(work_order.scheduled_date)

    def test_ordering_by_received_date_and_id_descending(self):
        older = self._create_work_order(
            number="1001",
            received_date=date(2026, 9, 1),
        )
        newer_first = self._create_work_order(
            number="1002",
            received_date=date(2026, 9, 20),
        )
        newer_second = self._create_work_order(
            number="1003",
            received_date=date(2026, 9, 20),
        )

        orders = list(WorkOrder.objects.all())

        self.assertEqual(orders, [newer_second, newer_first, older])


class WorkOrderItemModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="comercial.items")
        self.customer = Customer.objects.create(trade_name="Seguridad Andina")
        self.work_type = WorkType.objects.create(name="Mantenimiento")
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

    def test_associate_product_with_requested_quantity(self):
        item = WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("2.00"),
        )

        self.assertIsNotNone(item.pk)
        self.assertEqual(item.work_order, self.work_order)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.requested_quantity, Decimal("2.00"))

    def test_str_identifies_order_product_and_quantity(self):
        item = WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("3.50"),
        )

        self.assertEqual(str(item), "OT 9101 - Cámara IP 4MP x 3.50")

    def test_work_order_can_have_multiple_items(self):
        cable = Product.objects.create(
            name="Cable UTP Cat6",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )
        WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("1.00"),
        )
        WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=cable,
            requested_quantity=Decimal("25.00"),
        )

        self.assertEqual(self.work_order.items.count(), 2)

    def test_requested_quantity_cannot_be_zero(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkOrderItem.objects.create(
                    work_order=self.work_order,
                    product=self.product,
                    requested_quantity=Decimal("0.00"),
                )

    def test_requested_quantity_cannot_be_negative(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkOrderItem.objects.create(
                    work_order=self.work_order,
                    product=self.product,
                    requested_quantity=Decimal("-1.00"),
                )


class WorkOrderHistoryModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="comercial.history")
        self.customer = Customer.objects.create(trade_name="Norte Electrónica")
        self.work_type = WorkType.objects.create(name="Soporte técnico")
        self.work_order = WorkOrder.objects.create(
            number="9202",
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            received_date=date(2026, 9, 14),
            created_by=self.user,
        )

    def test_create_history_event(self):
        entry = WorkOrderHistory.objects.create(
            work_order=self.work_order,
            user=self.user,
            event_type=WorkOrderHistory.EventType.CREATED,
            description="Orden de trabajo creada.",
        )

        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.work_order, self.work_order)
        self.assertEqual(entry.user, self.user)

    def test_event_type_created(self):
        entry = WorkOrderHistory.objects.create(
            work_order=self.work_order,
            user=self.user,
            event_type=WorkOrderHistory.EventType.CREATED,
            description="Registro inicial.",
        )

        self.assertEqual(entry.event_type, WorkOrderHistory.EventType.CREATED)

    def test_ordering_by_created_at_descending(self):
        older = WorkOrderHistory.objects.create(
            work_order=self.work_order,
            user=self.user,
            event_type=WorkOrderHistory.EventType.CREATED,
            description="Evento anterior.",
        )
        newer = WorkOrderHistory.objects.create(
            work_order=self.work_order,
            user=self.user,
            event_type=WorkOrderHistory.EventType.UPDATED,
            description="Evento posterior.",
        )
        WorkOrderHistory.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(hours=1),
        )
        WorkOrderHistory.objects.filter(pk=newer.pk).update(
            created_at=timezone.now(),
        )

        events = list(WorkOrderHistory.objects.all())

        self.assertEqual(events, [newer, older])

    def test_previous_and_new_value_can_be_empty(self):
        entry = WorkOrderHistory.objects.create(
            work_order=self.work_order,
            user=self.user,
            event_type=WorkOrderHistory.EventType.CREATED,
            description="Sin valores previos ni nuevos.",
        )

        self.assertEqual(entry.previous_value, "")
        self.assertEqual(entry.new_value, "")
