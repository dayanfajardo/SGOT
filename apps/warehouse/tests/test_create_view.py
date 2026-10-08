from datetime import date
from decimal import Decimal

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
from apps.catalog.models import Product, ProductCategory, Technician, WorkType
from apps.customers.models import Customer
from apps.warehouse.models import WarehouseOutput, WarehouseOutputItem
from apps.workorders.models import WorkOrder, WorkOrderItem

User = get_user_model()


class WarehouseOutputCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        add_permission = Permission.objects.get(
            content_type__app_label="warehouse",
            codename="add_warehouseoutput",
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
        for group in (
            self.commercial_group,
            self.technical_group,
            self.management_group,
        ):
            group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Salida")
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

        self.work_order = self._create_work_order(number="9101")
        self.work_order_item = WorkOrderItem.objects.create(
            work_order=self.work_order,
            product=self.product,
            requested_quantity=Decimal("2.00"),
        )
        self.url = reverse(
            "warehouse:warehouse_output_create",
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
            "items-TOTAL_FORMS": str(len(items)),
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
        }
        for index, item in enumerate(items):
            data[f"items-{index}-work_order_item"] = item.get(
                "work_order_item",
                "",
            )
            data[f"items-{index}-product"] = item.get("product", "")
            data[f"items-{index}-delivered_quantity"] = item.get(
                "delivered_quantity",
                "",
            )
            data[f"items-{index}-notes"] = item.get("notes", "")
            data[f"items-{index}-DELETE"] = item.get("DELETE", "")
        return data

    def _valid_post_data(self, *, items=None, **overrides):
        if items is None:
            items = [
                {
                    "work_order_item": str(self.work_order_item.pk),
                    "delivered_quantity": "2.00",
                }
            ]

        data = {
            "number": "5400",
            "output_date": "2026-09-22",
            "notes": "Entrega de equipos.",
        }
        data.update(self._formset_data(items))
        data.update(overrides)
        return data

    def _post_create(self, user, data=None, work_order=None):
        work_order = work_order or self.work_order
        self.client.force_login(user)
        url = reverse(
            "warehouse:warehouse_output_create",
            args=[work_order.pk],
        )
        return self.client.post(url, data or self._valid_post_data())

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

    def test_create_uses_warehouse_output_form_template(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(
            response,
            "warehouse/warehouse_output_form.html",
        )

    def test_valid_post_creates_output_for_equipment_ok_order(self):
        response = self._post_create(self.admin_user)

        self.assertRedirects(response, self.detail_url)
        self.assertTrue(WarehouseOutput.objects.filter(number="5400").exists())

    def test_output_is_associated_to_the_work_order(self):
        self._post_create(self.admin_user)

        output = WarehouseOutput.objects.get(number="5400")

        self.assertEqual(output.work_order, self.work_order)

    def test_output_technician_is_assigned_technician(self):
        self._post_create(self.admin_user)

        output = WarehouseOutput.objects.get(number="5400")

        self.assertEqual(output.technician, self.technician)

    def test_created_by_is_authenticated_user(self):
        self._post_create(self.admin_user)

        output = WarehouseOutput.objects.get(number="5400")

        self.assertEqual(output.created_by, self.admin_user)

    def test_item_from_work_order_item_infers_product(self):
        self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": str(self.work_order_item.pk),
                        "product": "",
                        "delivered_quantity": "2.00",
                    }
                ]
            ),
        )

        item = WarehouseOutputItem.objects.get()

        self.assertEqual(item.work_order_item, self.work_order_item)
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.delivered_quantity, Decimal("2.00"))

    def test_additional_material_without_work_order_item(self):
        self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": "",
                        "product": str(self.extra_product.pk),
                        "delivered_quantity": "5.00",
                    }
                ]
            ),
        )

        item = WarehouseOutputItem.objects.get()

        self.assertIsNone(item.work_order_item)
        self.assertEqual(item.product, self.extra_product)
        self.assertEqual(item.delivered_quantity, Decimal("5.00"))

    def test_creates_multiple_items(self):
        self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": str(self.work_order_item.pk),
                        "delivered_quantity": "2.00",
                    },
                    {
                        "product": str(self.extra_product.pk),
                        "delivered_quantity": "5.00",
                    },
                ]
            ),
        )

        output = WarehouseOutput.objects.get(number="5400")
        items = list(output.items.order_by("id"))

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].work_order_item, self.work_order_item)
        self.assertEqual(items[0].product, self.product)
        self.assertIsNone(items[1].work_order_item)
        self.assertEqual(items[1].product, self.extra_product)

    def test_duplicate_work_order_item_does_not_create_output(self):
        response = self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": str(self.work_order_item.pk),
                        "delivered_quantity": "1.00",
                    },
                    {
                        "work_order_item": str(self.work_order_item.pk),
                        "delivered_quantity": "1.00",
                    },
                ]
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 0)
        self.assertEqual(WarehouseOutputItem.objects.count(), 0)

    def test_row_without_item_or_product_does_not_create_output(self):
        response = self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": "",
                        "product": "",
                        "delivered_quantity": "2.00",
                    }
                ]
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 0)
        self.assertEqual(WarehouseOutputItem.objects.count(), 0)

    def test_row_with_item_and_product_does_not_create_output(self):
        response = self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": str(self.work_order_item.pk),
                        "product": str(self.extra_product.pk),
                        "delivered_quantity": "2.00",
                    }
                ]
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 0)
        self.assertEqual(WarehouseOutputItem.objects.count(), 0)

    def test_order_not_equipment_ok_does_not_create_output(self):
        work_order = self._create_work_order(
            number="9102",
            status=WorkOrder.Status.RECEIVED,
        )
        data = self._valid_post_data(
            items=[
                {
                    "product": str(self.extra_product.pk),
                    "delivered_quantity": "1.00",
                }
            ]
        )

        response = self._post_create(
            self.admin_user,
            data,
            work_order=work_order,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 0)

    def test_order_without_technician_does_not_create_output(self):
        work_order = self._create_work_order(
            number="9103",
            assigned_technician=None,
        )
        data = self._valid_post_data(
            items=[
                {
                    "product": str(self.extra_product.pk),
                    "delivered_quantity": "1.00",
                }
            ]
        )

        response = self._post_create(
            self.admin_user,
            data,
            work_order=work_order,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 0)

    def test_existing_output_does_not_allow_another(self):
        WarehouseOutput.objects.create(
            number="5399",
            work_order=self.work_order,
            technician=self.technician,
            output_date=date(2026, 9, 20),
            created_by=self.admin_user,
        )

        response = self._post_create(self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 1)
        self.assertFalse(WarehouseOutput.objects.filter(number="5400").exists())

    def test_failed_item_rolls_back_output(self):
        response = self._post_create(
            self.admin_user,
            self._valid_post_data(
                items=[
                    {
                        "work_order_item": str(self.work_order_item.pk),
                        "product": str(self.extra_product.pk),
                        "delivered_quantity": "2.00",
                    }
                ]
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WarehouseOutput.objects.count(), 0)
        self.assertEqual(WarehouseOutputItem.objects.count(), 0)
