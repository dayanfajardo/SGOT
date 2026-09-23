from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.catalog.models import Technician, WorkType
from apps.customers.models import Customer
from apps.workorders.models import WorkOrder

User = get_user_model()


class WorkOrderListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("workorders:workorder_list")

        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )

        self.commercial_group, _ = Group.objects.get_or_create(name="Comercial")
        self.admin_group, _ = Group.objects.get_or_create(
            name="Administrador / Almacén"
        )
        self.technical_group, _ = Group.objects.get_or_create(name="Jefe Técnica")
        self.management_group, _ = Group.objects.get_or_create(name="Gerencia")

        for group in (
            self.commercial_group,
            self.admin_group,
            self.technical_group,
            self.management_group,
        ):
            group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Lista")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )

        self.commercial = self._create_user("comercial.uno", self.commercial_group)
        self.other_commercial = self._create_user(
            "comercial.dos",
            self.commercial_group,
        )
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

        self.own_order = self._create_work_order(
            number="OT-1001",
            commercial=self.commercial,
        )
        self.other_order = self._create_work_order(
            number="OT-1002",
            commercial=self.other_commercial,
        )

    def _create_user(self, username, group):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )
        user.groups.add(group)
        return user

    def _create_work_order(self, *, number, commercial):
        return WorkOrder.objects.create(
            number=number,
            customer=self.customer,
            commercial=commercial,
            work_type=self.work_type,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 10),
            created_by=commercial,
        )

    def _get_list(self, user):
        self.client.force_login(user)
        return self.client.get(self.url)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_commercial_sees_only_own_orders(self):
        response = self._get_list(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertEqual(list(response.context["work_orders"]), [self.own_order])

    def test_commercial_does_not_see_other_commercial_orders(self):
        response = self._get_list(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.other_order.number)
        self.assertNotIn(self.other_order, response.context["work_orders"])

    def test_admin_warehouse_sees_all_orders(self):
        response = self._get_list(self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.other_order.number)

    def test_technical_manager_sees_all_orders(self):
        response = self._get_list(self.technical_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.other_order.number)

    def test_management_sees_all_orders(self):
        response = self._get_list(self.management_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.other_order.number)

    def test_list_uses_workorder_list_template(self):
        response = self._get_list(self.admin_user)

        self.assertTemplateUsed(response, "workorders/workorder_list.html")
