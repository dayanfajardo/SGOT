from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.constants import ADMIN_WAREHOUSE_GROUP
from apps.catalog.models import Product, ProductCategory, Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.services import (
    add_output_item,
    create_warehouse_output,
    update_returned_quantity,
)
from apps.workorders.models import WorkOrder

User = get_user_model()


class WarehouseOutputReturnsViewTests(TestCase):
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

        self.customer = Customer.objects.create(trade_name="Cliente Devoluciones")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.product = Product.objects.create(
            name="Cámara IP 4MP",
            product_code="1-1-1",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.extra_product = Product.objects.create(
            name="Cable UTP Cat6",
            product_code="1-5-1",
            category=ProductCategory.MATERIALS_ACCESSORIES,
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )

        self.admin_user = self._create_user("admin.almacen", self.admin_group)
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.work_order = self._create_work_order(number="9401")
        self.output = create_warehouse_output(
            number="5501",
            work_order=self.work_order,
            technician=self.technician,
            output_date=date(2026, 9, 22),
            created_by=self.admin_user,
        )
        self.item_one = add_output_item(
            warehouse_output=self.output,
            product=self.product,
            delivered_quantity=Decimal("4.00"),
        )
        self.item_two = add_output_item(
            warehouse_output=self.output,
            product=self.extra_product,
            delivered_quantity=Decimal("10.00"),
        )
        update_returned_quantity(
            output_item=self.item_one,
            returned_quantity=Decimal("1.50"),
        )

        self.url = reverse(
            "warehouse:warehouse_output_returns",
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
            "received_date": date(2026, 9, 12),
            "created_by": self.admin_user,
        }
        data.update(overrides)
        return WorkOrder.objects.create(**data)

    def _formset_data(self, items):
        data = {
            "form-TOTAL_FORMS": str(len(items)),
            "form-INITIAL_FORMS": str(len(items)),
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        for index, item in enumerate(items):
            data[f"form-{index}-item_id"] = str(item["item_id"])
            data[f"form-{index}-returned_quantity"] = str(
                item["returned_quantity"]
            )
        return data

    def _valid_post_data(self, **overrides):
        data = self._formset_data(
            [
                {
                    "item_id": self.item_one.pk,
                    "returned_quantity": "2.00",
                },
                {
                    "item_id": self.item_two.pk,
                    "returned_quantity": "3.00",
                },
            ]
        )
        data.update(overrides)
        return data

    def _post_returns(self, user, data=None, output=None):
        output = output or self.output
        self.client.force_login(user)
        url = reverse(
            "warehouse:warehouse_output_returns",
            args=[output.pk],
        )
        return self.client.post(url, data or self._valid_post_data())

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.force_login(self.user_without_permission)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_admin_warehouse_can_open_returns_form(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_get_creates_one_form_per_output_item(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)
        formset = response.context["formset"]
        items = list(response.context["items"])

        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(len(items), 2)
        self.assertEqual(
            [form.initial["item_id"] for form in formset.forms],
            [self.item_one.pk, self.item_two.pk],
        )

    def test_get_initial_returned_quantities_match_saved_values(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)
        formset = response.context["formset"]

        self.assertEqual(
            formset.forms[0].initial["returned_quantity"],
            Decimal("1.50"),
        )
        self.assertEqual(
            formset.forms[1].initial["returned_quantity"],
            Decimal("0.00"),
        )

    def test_valid_post_updates_returned_quantities(self):
        response = self._post_returns(self.admin_user)

        self.assertRedirects(response, self.detail_url)
        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        self.assertEqual(self.item_one.returned_quantity, Decimal("2.00"))
        self.assertEqual(self.item_two.returned_quantity, Decimal("3.00"))

    @patch("apps.warehouse.views.update_returned_quantity")
    def test_post_does_not_update_quantities_outside_service(self, mock_update):
        mock_update.return_value = self.item_one

        self._post_returns(self.admin_user)

        self.assertTrue(mock_update.called)
        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        self.assertEqual(self.item_one.returned_quantity, Decimal("1.50"))
        self.assertEqual(self.item_two.returned_quantity, Decimal("0.00"))

    def test_quantity_over_delivered_does_not_save_partial_changes(self):
        response = self._post_returns(
            self.admin_user,
            self._formset_data(
                [
                    {
                        "item_id": self.item_one.pk,
                        "returned_quantity": "2.00",
                    },
                    {
                        "item_id": self.item_two.pk,
                        "returned_quantity": "99.00",
                    },
                ]
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        self.assertEqual(self.item_one.returned_quantity, Decimal("1.50"))
        self.assertEqual(self.item_two.returned_quantity, Decimal("0.00"))

    def test_tampered_item_id_from_another_output_does_not_change_items(self):
        other_order = self._create_work_order(number="9402")
        other_output = create_warehouse_output(
            number="5502",
            work_order=other_order,
            technician=self.technician,
            output_date=date(2026, 9, 23),
            created_by=self.admin_user,
        )
        other_item = add_output_item(
            warehouse_output=other_output,
            product=self.product,
            delivered_quantity=Decimal("2.00"),
        )

        response = self._post_returns(
            self.admin_user,
            self._formset_data(
                [
                    {
                        "item_id": self.item_one.pk,
                        "returned_quantity": "2.00",
                    },
                    {
                        "item_id": other_item.pk,
                        "returned_quantity": "1.00",
                    },
                ]
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.item_one.refresh_from_db()
        self.item_two.refresh_from_db()
        other_item.refresh_from_db()
        self.assertEqual(self.item_one.returned_quantity, Decimal("1.50"))
        self.assertEqual(self.item_two.returned_quantity, Decimal("0.00"))
        self.assertEqual(other_item.returned_quantity, Decimal("0.00"))

    def test_reconciled_output_cannot_be_edited(self):
        self.output.reconciled_at = timezone.now()
        self.output.reconciled_by = self.admin_user
        self.output.save()
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
