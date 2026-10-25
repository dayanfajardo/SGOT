from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.catalog.models import Technician, WorkType
from apps.customers.models import Customer
from apps.workorders.models import WorkOrder, WorkOrderHistory

User = get_user_model()

RESCHEDULE_REASON_ERROR = "Debe indicar el motivo de la reprogramación."


class WorkOrderScheduleViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        schedule_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="schedule_workorder",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )
        change_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="change_workorder",
        )

        self.customer = Customer.objects.create(trade_name="Cliente Programación")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
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

        self.scheduler = User.objects.create_user(
            username="jefe.programacion",
            email="jefe.programacion@example.com",
            password="pass",
        )
        self.scheduler.user_permissions.add(
            schedule_permission,
            view_permission,
        )
        self.user_without_schedule_permission = User.objects.create_user(
            username="operador.sin.programacion",
            email="operador.sin.programacion@example.com",
            password="pass",
        )
        self.user_without_schedule_permission.user_permissions.add(
            view_permission,
            change_permission,
        )

        self.commercial = self.scheduler

    def _create_work_order(self, *, number, scheduled_date=None, technician=None):
        return WorkOrder.objects.create(
            number=number,
            customer=self.customer,
            commercial=self.commercial,
            work_type=self.work_type,
            status=WorkOrder.Status.EQUIPMENT_OK,
            assigned_technician=technician,
            scheduled_date=scheduled_date,
            received_date=date(2026, 10, 1),
            created_by=self.scheduler,
        )

    def _schedule_url(self, work_order):
        return reverse("workorders:workorder_schedule", args=[work_order.pk])

    def _detail_url(self, work_order):
        return reverse("workorders:workorder_detail", args=[work_order.pk])

    def _post_schedule(self, user, work_order, **data):
        self.client.force_login(user)
        return self.client.post(self._schedule_url(work_order), data)

    def test_initial_schedule_without_reason_is_valid(self):
        work_order = self._create_work_order(number="OT-7101")
        scheduled_date = date(2026, 10, 22)

        response = self._post_schedule(
            self.scheduler,
            work_order,
            technician=self.technician.pk,
            scheduled_date=scheduled_date.isoformat(),
        )

        self.assertRedirects(response, self._detail_url(work_order))
        work_order.refresh_from_db()
        self.assertEqual(work_order.scheduled_date, scheduled_date)
        self.assertEqual(work_order.assigned_technician, self.technician)
        self.assertTrue(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.SCHEDULED,
            ).exists()
        )

    def test_initial_schedule_with_empty_reason_is_valid(self):
        work_order = self._create_work_order(number="OT-7102")
        scheduled_date = date(2026, 10, 22)

        response = self._post_schedule(
            self.scheduler,
            work_order,
            technician=self.technician.pk,
            scheduled_date=scheduled_date.isoformat(),
            reschedule_reason="",
        )

        self.assertRedirects(response, self._detail_url(work_order))
        work_order.refresh_from_db()
        self.assertEqual(work_order.scheduled_date, scheduled_date)
        history = WorkOrderHistory.objects.get(
            work_order=work_order,
            event_type=WorkOrderHistory.EventType.SCHEDULED,
        )
        self.assertNotIn("Motivo:", history.description)

    def test_changing_date_without_reason_is_invalid(self):
        previous_date = date(2026, 10, 22)
        work_order = self._create_work_order(
            number="OT-7103",
            technician=self.technician,
            scheduled_date=previous_date,
        )

        response = self._post_schedule(
            self.scheduler,
            work_order,
            technician=self.technician.pk,
            scheduled_date="2026-10-29",
            reschedule_reason="",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            RESCHEDULE_REASON_ERROR,
            response.context["schedule_form"].errors.get("reschedule_reason", []),
        )
        work_order.refresh_from_db()
        self.assertEqual(work_order.scheduled_date, previous_date)
        self.assertFalse(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.RESCHEDULED,
            ).exists()
        )

    def test_changing_date_with_reason_records_rescheduled_history(self):
        previous_date = date(2026, 10, 22)
        new_date = date(2026, 10, 29)
        reason = "Cliente solicitó aplazamiento"
        work_order = self._create_work_order(
            number="OT-7104",
            technician=self.technician,
            scheduled_date=previous_date,
        )

        response = self._post_schedule(
            self.scheduler,
            work_order,
            technician=self.technician.pk,
            scheduled_date=new_date.isoformat(),
            reschedule_reason=reason,
        )

        self.assertRedirects(response, self._detail_url(work_order))
        work_order.refresh_from_db()
        self.assertEqual(work_order.scheduled_date, new_date)

        history = WorkOrderHistory.objects.get(
            work_order=work_order,
            event_type=WorkOrderHistory.EventType.RESCHEDULED,
        )
        self.assertEqual(
            history.previous_value,
            f"{previous_date} | {self.technician}",
        )
        self.assertEqual(
            history.new_value,
            f"{new_date} | {self.technician}",
        )
        self.assertIn(f"Motivo: {reason}", history.description)

        detail = self.client.get(self._detail_url(work_order))
        self.assertContains(
            detail,
            (
                "Orden reprogramada del 22 oct 2026 al 29 oct 2026. "
                "Motivo: Cliente solicitó aplazamiento."
            ),
        )

    def test_changing_only_technician_does_not_require_reason(self):
        scheduled_date = date(2026, 10, 22)
        work_order = self._create_work_order(
            number="OT-7105",
            technician=self.technician,
            scheduled_date=scheduled_date,
        )

        response = self._post_schedule(
            self.scheduler,
            work_order,
            technician=self.second_technician.pk,
            scheduled_date=scheduled_date.isoformat(),
        )

        self.assertRedirects(response, self._detail_url(work_order))
        work_order.refresh_from_db()
        self.assertEqual(work_order.assigned_technician, self.second_technician)
        self.assertEqual(work_order.scheduled_date, scheduled_date)
        self.assertTrue(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.TECHNICIAN_CHANGED,
            ).exists()
        )
        self.assertFalse(
            WorkOrderHistory.objects.filter(
                work_order=work_order,
                event_type=WorkOrderHistory.EventType.RESCHEDULED,
            ).exists()
        )

    def test_submitting_same_date_does_not_require_reason(self):
        scheduled_date = date(2026, 10, 22)
        work_order = self._create_work_order(
            number="OT-7106",
            technician=self.technician,
            scheduled_date=scheduled_date,
        )

        response = self._post_schedule(
            self.scheduler,
            work_order,
            technician=self.technician.pk,
            scheduled_date=scheduled_date.isoformat(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            RESCHEDULE_REASON_ERROR,
            response.context["schedule_form"].errors.get("reschedule_reason", []),
        )
        self.assertContains(
            response,
            "No hay cambios en la programación de la orden.",
        )
        work_order.refresh_from_db()
        self.assertEqual(work_order.scheduled_date, scheduled_date)

    def test_user_without_schedule_permission_cannot_modify_schedule(self):
        scheduled_date = date(2026, 10, 22)
        work_order = self._create_work_order(
            number="OT-7107",
            technician=self.technician,
            scheduled_date=scheduled_date,
        )

        response = self._post_schedule(
            self.user_without_schedule_permission,
            work_order,
            technician=self.second_technician.pk,
            scheduled_date="2026-10-29",
            reschedule_reason="Cliente solicitó aplazamiento",
        )

        self.assertEqual(response.status_code, 403)
        work_order.refresh_from_db()
        self.assertEqual(work_order.scheduled_date, scheduled_date)
        self.assertEqual(work_order.assigned_technician, self.technician)
        self.assertFalse(work_order.history.exists())

    def test_reschedule_reason_is_shown_when_date_is_already_scheduled(self):
        work_order = self._create_work_order(
            number="OT-7108",
            technician=self.technician,
            scheduled_date=date(2026, 10, 22),
        )
        self.client.force_login(self.scheduler)

        response = self.client.get(self._detail_url(work_order))

        self.assertContains(response, "Motivo de reprogramación")
        self.assertContains(
            response,
            "Obligatorio si cambia la fecha actualmente programada.",
        )
        self.assertContains(response, 'name="reschedule_reason"')
        self.assertContains(response, "sgot-textarea-compact")

    def test_reschedule_reason_is_hidden_on_initial_schedule(self):
        work_order = self._create_work_order(number="OT-7109")
        self.client.force_login(self.scheduler)

        response = self.client.get(self._detail_url(work_order))

        self.assertContains(response, "Programación técnica")
        self.assertNotContains(response, "Motivo de reprogramación")
        self.assertNotContains(response, 'name="reschedule_reason"')
