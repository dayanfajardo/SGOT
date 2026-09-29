from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import ADMIN_WAREHOUSE_GROUP
from apps.catalog.models import Product, Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.services import (
    add_output_item,
    create_warehouse_output,
)
from apps.workorders.models import WorkOrder

User = get_user_model()


class WarehouseOutputReconcileViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        change_permission = Permission.objects.get(
            content_type__app_label="warehouse",
            codename="change_warehouseoutput",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )
        self.admin_group, _ = Group.objects.get_or_create(
            name=ADMIN_WAREHOUSE_GROUP
        )
        self.admin_group.permissions.add(change_permission, view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Conciliación")
        self.work_type = WorkType.objects.create(name="Instalación alarma")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.product = Product.objects.create(
            name="Sirena exterior",
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )

        self.admin_user = self._create_user("admin.almacen", self.admin_group)
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.work_order = self._create_work_order(number="9501")
        self.output = create_warehouse_output(
            number="5601",
            work_order=self.work_order,
            technician=self.technician,
            output_date=date(2026, 9, 22),
            created_by=self.admin_user,
        )
        add_output_item(
            warehouse_output=self.output,
            product=self.product,
            delivered_quantity=Decimal("4.00"),
        )
        self.work_order.status = WorkOrder.Status.IN_INSTALLATION
        self.work_order.save()

        self.url = reverse(
            "warehouse:warehouse_output_reconcile",
            args=[self.output.pk],
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

    def _create_work_order(self, *, number, **overrides):
        data = {
            "number": number,
            "customer": self.customer,
            "commercial": self.admin_user,
            "work_type": self.work_type,
            "status": WorkOrder.Status.EQUIPMENT_OK,
            "assigned_technician": self.technician,
            "received_date": date(2026, 9, 16),
            "created_by": self.admin_user,
        }
        data.update(overrides)
        return WorkOrder.objects.create(**data)

    def _post_reconcile(self, user, output=None):
        output = output or self.output
        self.client.force_login(user)
        url = reverse(
            "warehouse:warehouse_output_reconcile",
            args=[output.pk],
        )
        return self.client.post(url)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_get_is_not_allowed(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._post_reconcile(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_valid_post_redirects_to_work_order_detail(self):
        response = self._post_reconcile(self.admin_user)

        self.assertRedirects(response, self.detail_url)

    def test_valid_post_sets_reconciled_at_and_by(self):
        self._post_reconcile(self.admin_user)
        self.output.refresh_from_db()

        self.assertIsNotNone(self.output.reconciled_at)
        self.assertEqual(self.output.reconciled_by, self.admin_user)

    def test_already_reconciled_output_is_not_reconciled_again(self):
        self._post_reconcile(self.admin_user)
        self.output.refresh_from_db()
        reconciled_at = self.output.reconciled_at
        reconciled_by = self.output.reconciled_by

        response = self._post_reconcile(self.admin_user)

        self.assertRedirects(response, self.detail_url)
        self.output.refresh_from_db()
        self.assertEqual(self.output.reconciled_at, reconciled_at)
        self.assertEqual(self.output.reconciled_by, reconciled_by)

    def test_order_not_in_installation_cannot_be_reconciled(self):
        work_order = self._create_work_order(number="9502")
        output = create_warehouse_output(
            number="5602",
            work_order=work_order,
            technician=self.technician,
            output_date=date(2026, 9, 23),
            created_by=self.admin_user,
        )

        response = self._post_reconcile(self.admin_user, output)

        self.assertRedirects(
            response,
            reverse("workorders:workorder_detail", args=[work_order.pk]),
        )
        output.refresh_from_db()
        self.assertIsNone(output.reconciled_at)
        self.assertIsNone(output.reconciled_by)
