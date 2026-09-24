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


class WorkOrderCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("workorders:workorder_create")

        add_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="add_workorder",
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

        self.admin_group.permissions.add(add_permission, view_permission)
        self.commercial_group.permissions.add(view_permission)
        self.technical_group.permissions.add(view_permission)
        self.management_group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Creación")
        self.work_type = WorkType.objects.create(name="Instalación de alarma")
        self.product = Product.objects.create(
            name="Cámara IP 4MP",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.second_product = Product.objects.create(
            name="Cable UTP Cat6",
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
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

    def _create_user(self, username, group):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )
        user.groups.add(group)
        return user

    def _formset_data(self, items):
        data = {
            "items-TOTAL_FORMS": str(len(items)),
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
        }
        for index, item in enumerate(items):
            data[f"items-{index}-product"] = item.get("product", "")
            data[f"items-{index}-requested_quantity"] = item.get("quantity", "")
            data[f"items-{index}-notes"] = item.get("notes", "")
        return data

    def _valid_post_data(self, *, number="OT-2001", items=None, **overrides):
        if items is None:
            items = [{"product": str(self.product.pk), "quantity": "2"}]

        data = {
            "number": number,
            "customer": str(self.customer.pk),
            "commercial": str(self.commercial.pk),
            "work_type": str(self.work_type.pk),
            "received_date": "2026-09-21",
            "installation_address": "Calle 10 #20-30",
            "notes": "Notas de la OT",
        }
        data.update(self._formset_data(items))
        data.update(overrides)
        return data

    def _post_create(self, user, data=None):
        self.client.force_login(user)
        return self.client.post(self.url, data or self._valid_post_data())

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.force_login(self.user_without_permission)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_admin_warehouse_can_open_create_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_create_uses_workorder_form_template(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "workorders/workorder_form.html")

    def test_valid_post_creates_work_order(self):
        response = self._post_create(self.admin_user)

        self.assertRedirects(response, reverse("workorders:workorder_list"))
        self.assertTrue(WorkOrder.objects.filter(number="OT-2001").exists())

    def test_created_work_order_status_is_received(self):
        self._post_create(self.admin_user)

        work_order = WorkOrder.objects.get(number="OT-2001")

        self.assertEqual(work_order.status, WorkOrder.Status.RECEIVED)

    def test_created_by_is_authenticated_user(self):
        self._post_create(self.admin_user)

        work_order = WorkOrder.objects.get(number="OT-2001")

        self.assertEqual(work_order.created_by, self.admin_user)

    def test_create_creates_created_history(self):
        self._post_create(self.admin_user)

        work_order = WorkOrder.objects.get(number="OT-2001")
        history = WorkOrderHistory.objects.get(work_order=work_order)

        self.assertEqual(history.event_type, WorkOrderHistory.EventType.CREATED)
        self.assertEqual(history.user, self.admin_user)
        self.assertEqual(history.previous_value, "")
        self.assertEqual(history.new_value, WorkOrder.Status.RECEIVED)
        self.assertIn(work_order.number, history.description)

    def test_valid_post_creates_multiple_items(self):
        data = self._valid_post_data(
            items=[
                {"product": str(self.product.pk), "quantity": "2"},
                {"product": str(self.second_product.pk), "quantity": "5"},
            ]
        )

        self._post_create(self.admin_user, data)

        work_order = WorkOrder.objects.get(number="OT-2001")
        items = list(work_order.items.order_by("id"))

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].product, self.product)
        self.assertEqual(items[1].product, self.second_product)
        self.assertTrue(
            all(item.work_order == work_order for item in items)
        )
        self.assertEqual(WorkOrderItem.objects.count(), 2)

    def test_selected_commercial_is_saved(self):
        self._post_create(self.admin_user)

        work_order = WorkOrder.objects.get(number="OT-2001")

        self.assertEqual(work_order.commercial, self.commercial)

    def test_invalid_work_order_is_not_created(self):
        data = self._valid_post_data(number="")

        response = self._post_create(self.admin_user, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkOrder.objects.count(), 0)

    def test_invalid_formset_does_not_create_work_order(self):
        data = self._valid_post_data(
            items=[{"product": "", "quantity": "2"}]
        )

        response = self._post_create(self.admin_user, data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkOrder.objects.count(), 0)
        self.assertEqual(WorkOrderItem.objects.count(), 0)

    def test_commercial_cannot_create_work_order(self):
        response = self._post_create(self.commercial)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(WorkOrder.objects.count(), 0)

    def test_technical_manager_cannot_create_work_order(self):
        response = self._post_create(self.technical_user)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(WorkOrder.objects.count(), 0)

    def test_management_cannot_create_work_order(self):
        response = self._post_create(self.management_user)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(WorkOrder.objects.count(), 0)
