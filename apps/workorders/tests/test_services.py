from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.catalog.models import Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.models import WarehouseOutput
from apps.workorders.models import WorkOrder, WorkOrderHistory
from apps.workorders.services import (
    change_status,
    complete_work_order,
    create_work_order,
    schedule_work_order,
    start_installation,
)

User = get_user_model()


class WorkOrderServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dayan.services")

        self.customer = Customer.objects.create(
            trade_name="Cliente Servicios"
        )

        self.work_type = WorkType.objects.create(
            name="Instalación de alarma"
        )

        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )

        self.second_technician = Technician.objects.create(
            first_name="Andrés",
            last_name="Gómez",
            technician_type=Technician.TechnicianType.CONTRACTOR,
        )

        self.inactive_technician = Technician.objects.create(
            first_name="Técnico",
            last_name="Inactivo",
            technician_type=Technician.TechnicianType.CONTRACTOR,
            active=False,
        )

    def _create_work_order(
        self,
        *,
        number="8001",
        status=WorkOrder.Status.RECEIVED,
        technician=None,
        scheduled_date=None,
    ):
        return WorkOrder.objects.create(
            number=number,
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            status=status,
            assigned_technician=technician,
            scheduled_date=scheduled_date,
            received_date=date(2026, 9, 21),
            created_by=self.user,
        )

    def _create_work_order_via_service(
        self,
        *,
        number="9001",
        installation_address="",
        notes="",
    ):
        return create_work_order(
            number=number,
            customer=self.customer,
            commercial=self.user,
            work_type=self.work_type,
            received_date=date(2026, 9, 21),
            created_by=self.user,
            installation_address=installation_address,
            notes=notes,
        )

    def _create_warehouse_output(self, work_order, *, number="5256", reconciled=False):
        return WarehouseOutput.objects.create(
            number=number,
            work_order=work_order,
            technician=self.technician,
            output_date=date(2026, 9, 22),
            created_by=self.user,
            reconciled_at=timezone.now() if reconciled else None,
            reconciled_by=self.user if reconciled else None,
        )

    # change_status

    def test_received_can_change_to_pending_equipment(self):
        work_order = self._create_work_order()

        change_status(
            work_order=work_order,
            new_status=WorkOrder.Status.PENDING_EQUIPMENT,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.status,
            WorkOrder.Status.PENDING_EQUIPMENT,
        )

    def test_received_can_change_to_equipment_ok(self):
        work_order = self._create_work_order()

        change_status(
            work_order=work_order,
            new_status=WorkOrder.Status.EQUIPMENT_OK,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.status,
            WorkOrder.Status.EQUIPMENT_OK,
        )

    def test_pending_equipment_can_change_to_equipment_ok(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.PENDING_EQUIPMENT
        )

        change_status(
            work_order=work_order,
            new_status=WorkOrder.Status.EQUIPMENT_OK,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.status,
            WorkOrder.Status.EQUIPMENT_OK,
        )

    def test_change_status_rejects_same_status(self):
        work_order = self._create_work_order()

        with self.assertRaises(ValidationError):
            change_status(
                work_order=work_order,
                new_status=WorkOrder.Status.RECEIVED,
                actor=self.user,
            )

    def test_change_status_rejects_invalid_transition(self):
        work_order = self._create_work_order()

        with self.assertRaises(ValidationError):
            change_status(
                work_order=work_order,
                new_status=WorkOrder.Status.COMPLETED,
                actor=self.user,
            )

    def test_change_status_creates_history(self):
        work_order = self._create_work_order()

        change_status(
            work_order=work_order,
            new_status=WorkOrder.Status.PENDING_EQUIPMENT,
            actor=self.user,
        )

        history = WorkOrderHistory.objects.get(work_order=work_order)

        self.assertEqual(
            history.event_type,
            WorkOrderHistory.EventType.STATUS_CHANGED,
        )
        self.assertEqual(
            history.previous_value,
            WorkOrder.Status.RECEIVED,
        )
        self.assertEqual(
            history.new_value,
            WorkOrder.Status.PENDING_EQUIPMENT,
        )

    # schedule_work_order

    def test_equipment_ok_work_order_can_be_scheduled(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        scheduled_date = date(2026, 9, 25)

        schedule_work_order(
            work_order=work_order,
            technician=self.technician,
            scheduled_date=scheduled_date,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.assigned_technician,
            self.technician,
        )
        self.assertEqual(
            work_order.scheduled_date,
            scheduled_date,
        )

    def test_first_schedule_creates_scheduled_history(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        schedule_work_order(
            work_order=work_order,
            technician=self.technician,
            scheduled_date=date(2026, 9, 25),
            actor=self.user,
        )

        history = WorkOrderHistory.objects.get(
            work_order=work_order,
            event_type=WorkOrderHistory.EventType.SCHEDULED,
        )

        self.assertEqual(history.user, self.user)

    def test_changing_schedule_date_creates_rescheduled_history(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        schedule_work_order(
            work_order=work_order,
            technician=self.technician,
            scheduled_date=date(2026, 9, 25),
            actor=self.user,
        )

        schedule_work_order(
            work_order=work_order,
            technician=self.technician,
            scheduled_date=date(2026, 9, 27),
            actor=self.user,
        )

        self.assertTrue(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.RESCHEDULED,
            ).exists()
        )

    def test_changing_only_technician_creates_history(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        scheduled_date = date(2026, 9, 25)

        schedule_work_order(
            work_order=work_order,
            technician=self.technician,
            scheduled_date=scheduled_date,
            actor=self.user,
        )

        schedule_work_order(
            work_order=work_order,
            technician=self.second_technician,
            scheduled_date=scheduled_date,
            actor=self.user,
        )

        self.assertTrue(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.TECHNICIAN_CHANGED,
            ).exists()
        )

    def test_cannot_schedule_if_status_is_not_equipment_ok(self):
        work_order = self._create_work_order()

        with self.assertRaises(ValidationError):
            schedule_work_order(
                work_order=work_order,
                technician=self.technician,
                scheduled_date=date(2026, 9, 25),
                actor=self.user,
            )

    def test_cannot_schedule_with_inactive_technician(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        with self.assertRaises(ValidationError):
            schedule_work_order(
                work_order=work_order,
                technician=self.inactive_technician,
                scheduled_date=date(2026, 9, 25),
                actor=self.user,
            )

    def test_cannot_schedule_without_technician(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        with self.assertRaises(ValidationError):
            schedule_work_order(
                work_order=work_order,
                technician=None,
                scheduled_date=date(2026, 9, 25),
                actor=self.user,
            )

    def test_cannot_schedule_without_date(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        with self.assertRaises(ValidationError):
            schedule_work_order(
                work_order=work_order,
                technician=self.technician,
                scheduled_date=None,
                actor=self.user,
            )

    def test_same_schedule_is_rejected(self):
        scheduled_date = date(2026, 9, 25)

        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )

        schedule_work_order(
            work_order=work_order,
            technician=self.technician,
            scheduled_date=scheduled_date,
            actor=self.user,
        )

        with self.assertRaises(ValidationError):
            schedule_work_order(
                work_order=work_order,
                technician=self.technician,
                scheduled_date=scheduled_date,
                actor=self.user,
            )

    # start_installation

    def test_start_installation_changes_status(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK,
            technician=self.technician,
            scheduled_date=date(2026, 9, 25),
        )

        start_installation(
            work_order=work_order,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.status,
            WorkOrder.Status.IN_INSTALLATION,
        )

    def test_start_installation_sets_timestamp(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK,
            technician=self.technician,
            scheduled_date=date(2026, 9, 25),
        )

        start_installation(
            work_order=work_order,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertIsNotNone(work_order.installation_started_at)

    def test_start_installation_creates_history(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK,
            technician=self.technician,
            scheduled_date=date(2026, 9, 25),
        )

        start_installation(
            work_order=work_order,
            actor=self.user,
        )

        self.assertTrue(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.INSTALLATION_STARTED,
            ).exists()
        )

    def test_cannot_start_installation_from_invalid_status(self):
        work_order = self._create_work_order()

        with self.assertRaises(ValidationError):
            start_installation(
                work_order=work_order,
                actor=self.user,
            )

    def test_cannot_start_without_technician_or_date(self):
        without_technician = self._create_work_order(
            number="8101",
            status=WorkOrder.Status.EQUIPMENT_OK,
            scheduled_date=date(2026, 9, 25),
        )

        without_date = self._create_work_order(
            number="8102",
            status=WorkOrder.Status.EQUIPMENT_OK,
            technician=self.technician,
        )

        with self.assertRaises(ValidationError):
            start_installation(
                work_order=without_technician,
                actor=self.user,
            )

        with self.assertRaises(ValidationError):
            start_installation(
                work_order=without_date,
                actor=self.user,
            )

    # complete_work_order

    def test_complete_work_order_changes_status(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.IN_INSTALLATION
        )
        self._create_warehouse_output(work_order, reconciled=True)

        complete_work_order(
            work_order=work_order,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.status,
            WorkOrder.Status.COMPLETED,
        )

    def test_complete_work_order_sets_timestamp(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.IN_INSTALLATION
        )
        self._create_warehouse_output(work_order, reconciled=True)

        complete_work_order(
            work_order=work_order,
            actor=self.user,
        )

        work_order.refresh_from_db()

        self.assertIsNotNone(work_order.completed_at)

    def test_complete_work_order_creates_history(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.IN_INSTALLATION
        )
        self._create_warehouse_output(work_order, reconciled=True)

        complete_work_order(
            work_order=work_order,
            actor=self.user,
        )

        history = WorkOrderHistory.objects.get(
            work_order=work_order,
            event_type=WorkOrderHistory.EventType.COMPLETED,
        )

        self.assertEqual(history.user, self.user)
        self.assertEqual(
            history.previous_value,
            WorkOrder.Status.IN_INSTALLATION,
        )
        self.assertEqual(
            history.new_value,
            WorkOrder.Status.COMPLETED,
        )

    def test_cannot_complete_work_order_from_invalid_status(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.EQUIPMENT_OK
        )
        self._create_warehouse_output(work_order, reconciled=True)

        with self.assertRaises(ValidationError):
            complete_work_order(
                work_order=work_order,
                actor=self.user,
            )

        work_order.refresh_from_db()
        self.assertEqual(work_order.status, WorkOrder.Status.EQUIPMENT_OK)
        self.assertIsNone(work_order.completed_at)

    def test_cannot_complete_without_warehouse_output(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.IN_INSTALLATION
        )

        with self.assertRaises(ValidationError):
            complete_work_order(
                work_order=work_order,
                actor=self.user,
            )

        work_order.refresh_from_db()
        self.assertEqual(work_order.status, WorkOrder.Status.IN_INSTALLATION)
        self.assertIsNone(work_order.completed_at)

    def test_cannot_complete_with_unreconciled_output(self):
        work_order = self._create_work_order(
            status=WorkOrder.Status.IN_INSTALLATION
        )
        self._create_warehouse_output(work_order, reconciled=False)

        with self.assertRaises(ValidationError):
            complete_work_order(
                work_order=work_order,
                actor=self.user,
            )

        work_order.refresh_from_db()
        self.assertEqual(work_order.status, WorkOrder.Status.IN_INSTALLATION)
        self.assertIsNone(work_order.completed_at)

    # create_work_order

    def test_create_work_order_creates_order(self):
        work_order = self._create_work_order_via_service()

        self.assertTrue(
            WorkOrder.objects.filter(pk=work_order.pk).exists()
        )

    def test_create_work_order_uses_received_status(self):
        work_order = self._create_work_order_via_service()

        work_order.refresh_from_db()

        self.assertEqual(
            work_order.status,
            WorkOrder.Status.RECEIVED,
        )

    def test_create_work_order_persists_fields(self):
        installation_address = "Calle 10 #20-30"
        notes = "Notas de la OT"

        work_order = self._create_work_order_via_service(
            number="9001",
            installation_address=installation_address,
            notes=notes,
        )

        work_order.refresh_from_db()

        self.assertEqual(work_order.number, "9001")
        self.assertEqual(work_order.customer, self.customer)
        self.assertEqual(work_order.commercial, self.user)
        self.assertEqual(work_order.work_type, self.work_type)
        self.assertEqual(work_order.received_date, date(2026, 9, 21))
        self.assertEqual(work_order.created_by, self.user)
        self.assertEqual(
            work_order.installation_address,
            installation_address,
        )
        self.assertEqual(work_order.notes, notes)

    def test_create_work_order_creates_exactly_one_history(self):
        work_order = self._create_work_order_via_service()

        self.assertEqual(
            WorkOrderHistory.objects.filter(work_order=work_order).count(),
            1,
        )

    def test_create_work_order_creates_history(self):
        work_order = self._create_work_order_via_service(number="9001")

        history = WorkOrderHistory.objects.get(work_order=work_order)

        self.assertEqual(
            history.event_type,
            WorkOrderHistory.EventType.CREATED,
        )
        self.assertEqual(history.user, self.user)
        self.assertEqual(history.previous_value, "")
        self.assertEqual(
            history.new_value,
            WorkOrder.Status.RECEIVED,
        )
        self.assertIn(work_order.number, history.description)

    def test_create_work_order_returns_persisted_order(self):
        work_order = self._create_work_order_via_service()

        persisted = WorkOrder.objects.get(pk=work_order.pk)

        self.assertEqual(work_order, persisted)