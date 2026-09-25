from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import (
    ADMIN_WAREHOUSE_GROUP,
    COMMERCIAL_GROUP,
    MANAGEMENT_GROUP,
    TECHNICAL_MANAGER_GROUP,
)
from apps.catalog.models import Technician, WorkType
from apps.customers.models import Customer
from apps.workorders.models import WorkOrder, WorkOrderHistory

User = get_user_model()


class WorkOrderStartInstallationViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        change_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="change_workorder",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )

        self.admin_group, _ = Group.objects.get_or_create(
            name=ADMIN_WAREHOUSE_GROUP
        )
        self.commercial_group, _ = Group.objects.get_or_create(
            name=COMMERCIAL_GROUP
        )
        self.technical_group, _ = Group.objects.get_or_create(
            name=TECHNICAL_MANAGER_GROUP
        )
        self.management_group, _ = Group.objects.get_or_create(
            name=MANAGEMENT_GROUP
        )

        self.admin_group.permissions.add(change_permission, view_permission)
        for group in (
            self.commercial_group,
            self.technical_group,
            self.management_group,
        ):
            group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Instalación")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )

        self.commercial = self._create_user("comercial.uno", self.commercial_group)
        self.admin_user = self._create_user("admin.almacen", self.admin_group)
        self.technical_user = self._create_user(
            "jefe.tecnica",
            self.technical_group,
        )
        self.management_user = self._create_user(
            "gerencia",
            self.management_group,
        )
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.work_order = self._create_ready_work_order(number="OT-4001")
        self.url = reverse(
            "workorders:workorder_start_installation",
            args=[self.work_order.pk],
        )
        self.detail_url = reverse(
            "workorders:workorder_detail",
            args=[self.work_order.pk],
        )

    def _create_user(self, username, group):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )
        user.groups.add(group)
        return user

    def _create_ready_work_order(self, *, number, **overrides):
        data = {
            "number": number,
            "customer": self.customer,
            "commercial": self.commercial,
            "work_type": self.work_type,
            "status": WorkOrder.Status.EQUIPMENT_OK,
            "assigned_technician": self.technician,
            "scheduled_date": date(2026, 9, 25),
            "received_date": date(2026, 9, 10),
            "created_by": self.admin_user,
        }
        data.update(overrides)
        return WorkOrder.objects.create(**data)

    def _post_start(self, user, work_order=None):
        work_order = work_order or self.work_order
        self.client.force_login(user)
        url = reverse(
            "workorders:workorder_start_installation",
            args=[work_order.pk],
        )
        return self.client.post(url)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._post_start(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_view_accepts_only_post(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_admin_warehouse_can_start_valid_installation(self):
        response = self._post_start(self.admin_user)

        self.assertRedirects(response, self.detail_url)

    def test_start_sets_in_installation_and_timestamp(self):
        self._post_start(self.admin_user)
        self.work_order.refresh_from_db()

        self.assertEqual(self.work_order.status, WorkOrder.Status.IN_INSTALLATION)
        self.assertIsNotNone(self.work_order.installation_started_at)

    def test_start_creates_installation_started_history(self):
        self._post_start(self.admin_user)

        self.assertTrue(
            WorkOrderHistory.objects.filter(
                work_order=self.work_order,
                event_type=WorkOrderHistory.EventType.INSTALLATION_STARTED,
                user=self.admin_user,
            ).exists()
        )

    def test_order_not_equipment_ok_does_not_change(self):
        work_order = self._create_ready_work_order(
            number="OT-4002",
            status=WorkOrder.Status.RECEIVED,
        )

        self._post_start(self.admin_user, work_order)
        work_order.refresh_from_db()

        self.assertEqual(work_order.status, WorkOrder.Status.RECEIVED)
        self.assertIsNone(work_order.installation_started_at)

    def test_order_without_technician_does_not_change(self):
        work_order = self._create_ready_work_order(
            number="OT-4003",
            assigned_technician=None,
        )

        self._post_start(self.admin_user, work_order)
        work_order.refresh_from_db()

        self.assertEqual(work_order.status, WorkOrder.Status.EQUIPMENT_OK)
        self.assertIsNone(work_order.installation_started_at)

    def test_order_without_scheduled_date_does_not_change(self):
        work_order = self._create_ready_work_order(
            number="OT-4004",
            scheduled_date=None,
        )

        self._post_start(self.admin_user, work_order)
        work_order.refresh_from_db()

        self.assertEqual(work_order.status, WorkOrder.Status.EQUIPMENT_OK)
        self.assertIsNone(work_order.installation_started_at)

    def test_validation_error_rerenders_detail_with_message(self):
        work_order = self._create_ready_work_order(
            number="OT-4005",
            status=WorkOrder.Status.RECEIVED,
        )

        response = self._post_start(self.admin_user, work_order)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "workorders/workorder_detail.html")
        self.assertContains(
            response,
            "Solo se puede iniciar la instalación si la orden está en Equipos OK.",
        )

    def test_commercial_cannot_start_installation(self):
        response = self._post_start(self.commercial)

        self.assertEqual(response.status_code, 403)
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, WorkOrder.Status.EQUIPMENT_OK)

    def test_technical_manager_cannot_start_installation(self):
        response = self._post_start(self.technical_user)

        self.assertEqual(response.status_code, 403)
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, WorkOrder.Status.EQUIPMENT_OK)

    def test_management_cannot_start_installation(self):
        response = self._post_start(self.management_user)

        self.assertEqual(response.status_code, 403)
        self.work_order.refresh_from_db()
        self.assertEqual(self.work_order.status, WorkOrder.Status.EQUIPMENT_OK)
