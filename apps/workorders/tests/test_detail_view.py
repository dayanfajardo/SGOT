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
from apps.catalog.models import Product, WorkType
from apps.customers.models import Customer
from apps.workorders.models import WorkOrder, WorkOrderHistory, WorkOrderItem

User = get_user_model()


class WorkOrderDetailViewTests(TestCase):
    def setUp(self):
        self.client = Client()

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

        for group in (
            self.admin_group,
            self.commercial_group,
            self.technical_group,
            self.management_group,
        ):
            group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Detalle")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.product = Product.objects.create(
            name="Cámara IP 4MP",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
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
            number="OT-3001",
            commercial=self.commercial,
        )
        self.other_order = self._create_work_order(
            number="OT-3002",
            commercial=self.other_commercial,
        )

        WorkOrderItem.objects.create(
            work_order=self.own_order,
            product=self.product,
            requested_quantity=2,
            notes="Ítem de detalle",
        )
        self.history = WorkOrderHistory.objects.create(
            work_order=self.own_order,
            user=self.admin_user,
            event_type=WorkOrderHistory.EventType.CREATED,
            description="Orden OT-3001 creada",
            new_value=WorkOrder.Status.RECEIVED,
        )

        self.url = reverse(
            "workorders:workorder_detail",
            args=[self.own_order.pk],
        )
        self.other_url = reverse(
            "workorders:workorder_detail",
            args=[self.other_order.pk],
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
            received_date=date(2026, 9, 10),
            installation_address="Calle 50 #10-20",
            notes="Notas de detalle",
            created_by=commercial,
        )

    def _get_detail(self, user, url=None):
        self.client.force_login(user)
        return self.client.get(url or self.url)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_detail(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_admin_warehouse_can_open_any_order(self):
        own_response = self._get_detail(self.admin_user)
        other_response = self._get_detail(self.admin_user, self.other_url)

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 200)

    def test_technical_manager_can_open_any_order(self):
        own_response = self._get_detail(self.technical_user)
        other_response = self._get_detail(self.technical_user, self.other_url)

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 200)

    def test_management_can_open_any_order(self):
        own_response = self._get_detail(self.management_user)
        other_response = self._get_detail(self.management_user, self.other_url)

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 200)

    def test_commercial_can_open_own_order(self):
        response = self._get_detail(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["work_order"], self.own_order)

    def test_commercial_cannot_open_other_commercial_order(self):
        response = self._get_detail(self.commercial, self.other_url)

        self.assertEqual(response.status_code, 404)

    def test_detail_uses_workorder_detail_template(self):
        response = self._get_detail(self.admin_user)

        self.assertTemplateUsed(response, "workorders/workorder_detail.html")

    def test_detail_contains_main_work_order_data(self):
        response = self._get_detail(self.admin_user)

        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.customer.trade_name)
        self.assertContains(response, self.work_type.name)
        self.assertContains(response, self.own_order.get_status_display())
        self.assertContains(response, self.own_order.installation_address)
        self.assertContains(response, self.own_order.notes)
        self.assertContains(response, str(self.own_order.commercial))

    def test_detail_shows_associated_products(self):
        response = self._get_detail(self.admin_user)

        self.assertContains(response, self.product.name)
        self.assertContains(response, "Ítem de detalle")

    def test_detail_shows_associated_history(self):
        response = self._get_detail(self.admin_user)

        self.assertContains(response, self.history.description)
        self.assertContains(response, self.history.get_event_type_display())
        self.assertContains(response, str(self.history.user))
