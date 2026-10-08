from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.constants import TECHNICAL_MANAGER_GROUP

User = get_user_model()


class TechnicalManagerCustomerPermissionTests(TestCase):
    def setUp(self):
        call_command("setup_roles")
        self.group = Group.objects.get(name=TECHNICAL_MANAGER_GROUP)

    def _has_customer_permission(self, codename):
        return self.group.permissions.filter(
            content_type__app_label="customers",
            codename=codename,
        ).exists()

    def test_technical_manager_has_view_customer(self):
        self.assertTrue(self._has_customer_permission("view_customer"))

    def test_technical_manager_does_not_have_add_customer(self):
        self.assertFalse(self._has_customer_permission("add_customer"))

    def test_technical_manager_does_not_have_change_customer(self):
        self.assertFalse(self._has_customer_permission("change_customer"))

    def test_technical_manager_does_not_have_delete_customer(self):
        self.assertFalse(self._has_customer_permission("delete_customer"))


class TechnicalManagerProductPermissionTests(TestCase):
    def setUp(self):
        call_command("setup_roles")
        self.group = Group.objects.get(name=TECHNICAL_MANAGER_GROUP)

    def _has_product_permission(self, codename):
        return self.group.permissions.filter(
            content_type__app_label="catalog",
            codename=codename,
        ).exists()

    def test_technical_manager_has_view_product(self):
        self.assertTrue(self._has_product_permission("view_product"))

    def test_technical_manager_does_not_have_add_product(self):
        self.assertFalse(self._has_product_permission("add_product"))

    def test_technical_manager_does_not_have_change_product(self):
        self.assertFalse(self._has_product_permission("change_product"))

    def test_technical_manager_does_not_have_delete_product(self):
        self.assertFalse(self._has_product_permission("delete_product"))


class ProductSidebarNavigationTests(TestCase):
    def setUp(self):
        self.products_url = reverse("catalog:product_list")
        self.technicians_url = reverse("catalog:technician_list")
        view_product = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_product",
        )
        view_technician = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_technician",
        )

        self.user_with_view_product = User.objects.create_user(
            username="con.productos",
            email="con.productos@example.com",
            password="pass",
        )
        self.user_with_view_product.user_permissions.add(view_product)
        self.user_without_view_product = User.objects.create_user(
            username="sin.productos",
            email="sin.productos@example.com",
            password="pass",
        )
        self.user_without_view_product.user_permissions.add(view_technician)

    def test_products_link_appears_with_view_product(self):
        self.client.force_login(self.user_with_view_product)
        response = self.client.get(self.products_url)

        self.assertContains(response, "Productos")
        self.assertContains(response, f'href="{self.products_url}"')

    def test_products_link_does_not_appear_without_view_product(self):
        self.client.force_login(self.user_without_view_product)
        response = self.client.get(self.technicians_url)

        self.assertNotContains(response, f'href="{self.products_url}"')
        self.assertNotContains(response, ">Productos</a>")
