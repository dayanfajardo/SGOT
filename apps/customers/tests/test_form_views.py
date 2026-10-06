from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.customers.models import Customer

User = get_user_model()


class CustomerCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("customers:customer_create")
        add_permission = Permission.objects.get(
            content_type__app_label="customers",
            codename="add_customer",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="customers",
            codename="view_customer",
        )

        self.user = User.objects.create_user(
            username="con.permiso",
            email="con.permiso@example.com",
            password="pass",
        )
        self.user.user_permissions.add(add_permission, view_permission)
        self.viewer = User.objects.create_user(
            username="solo.lectura",
            email="solo.lectura@example.com",
            password="pass",
        )
        self.viewer.user_permissions.add(view_permission)
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

    def _valid_data(self, **overrides):
        data = {
            "trade_name": "Nuevo Cliente",
            "legal_name": "Nuevo Cliente S.A.S.",
            "document": "900111222-3",
            "customer_code": "C-5000",
            "code_system": Customer.CodeSystem.CENTURION,
            "phone": "3000000000",
            "email": "nuevo@cliente.test",
        }
        data.update(overrides)
        return data

    def _post_create(self, user, data=None):
        self.client.force_login(user)
        return self.client.post(self.url, data or self._valid_data())

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.force_login(self.user_without_permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_user_with_add_permission_gets_200(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_valid_post_creates_customer(self):
        self._post_create(self.user)

        customer = Customer.objects.get(trade_name="Nuevo Cliente")
        self.assertEqual(customer.customer_code, "C-5000")
        self.assertEqual(customer.code_system, Customer.CodeSystem.CENTURION)

    def test_valid_post_redirects_to_detail(self):
        response = self._post_create(self.user)
        customer = Customer.objects.get(trade_name="Nuevo Cliente")

        self.assertRedirects(
            response,
            reverse("customers:customer_detail", args=[customer.pk]),
        )

    def test_invalid_post_does_not_create_customer(self):
        response = self._post_create(self.user, self._valid_data(trade_name=""))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), 0)

    def test_invalid_email_shows_form_error(self):
        response = self._post_create(
            self.user,
            self._valid_data(email="no-es-un-correo"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), 0)
        self.assertTrue(response.context["form"].errors["email"])

    def test_duplicate_customer_code_does_not_create_customer(self):
        Customer.objects.create(
            trade_name="Cliente Existente",
            customer_code="C-5000",
            code_system=Customer.CodeSystem.CENTURION,
        )

        response = self._post_create(self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertTrue(response.context["form"].errors["customer_code"])

    def test_duplicate_customer_code_in_different_system_does_not_create(self):
        Customer.objects.create(
            trade_name="Cliente Existente",
            customer_code="C-5000",
            code_system=Customer.CodeSystem.ARION,
        )

        response = self._post_create(self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Customer.objects.count(), 1)
        self.assertTrue(response.context["form"].errors["customer_code"])

    def test_new_customer_button_requires_add_permission(self):
        list_url = reverse("customers:customer_list")
        create_url = reverse("customers:customer_create")

        self.client.force_login(self.viewer)
        hidden = self.client.get(list_url)
        self.assertNotContains(hidden, "Nuevo cliente")
        self.assertNotContains(hidden, f'href="{create_url}"')

        self.client.force_login(self.user)
        visible = self.client.get(list_url)
        self.assertContains(visible, "Nuevo cliente")
        self.assertContains(visible, f'href="{create_url}"')


class CustomerUpdateViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="customers",
            codename="change_customer",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="customers",
            codename="view_customer",
        )

        self.user = User.objects.create_user(
            username="con.permiso",
            email="con.permiso@example.com",
            password="pass",
        )
        self.user.user_permissions.add(change_permission, view_permission)
        self.viewer = User.objects.create_user(
            username="solo.lectura",
            email="solo.lectura@example.com",
            password="pass",
        )
        self.viewer.user_permissions.add(view_permission)
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.customer = Customer.objects.create(
            customer_code="C-1001",
            code_system=Customer.CodeSystem.CENTURION,
            trade_name="Alarmas del Norte",
            legal_name="Alarmas del Norte S.A.S.",
            document="900123456-1",
            phone="3001234567",
            email="contacto@alarmasdelnorte.test",
        )
        self.url = reverse("customers:customer_update", args=[self.customer.pk])

    def _valid_data(self, **overrides):
        data = {
            "trade_name": self.customer.trade_name,
            "legal_name": self.customer.legal_name,
            "document": self.customer.document,
            "customer_code": self.customer.customer_code,
            "code_system": self.customer.code_system,
            "phone": self.customer.phone,
            "email": self.customer.email,
        }
        data.update(overrides)
        return data

    def _post_update(self, user, data=None, url=None):
        self.client.force_login(user)
        return self.client.post(url or self.url, data or self._valid_data())

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        self.client.force_login(self.user_without_permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_user_with_change_permission_gets_200(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_valid_post_updates_customer(self):
        self._post_update(self.user, self._valid_data(trade_name="Norte Actualizado"))

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.trade_name, "Norte Actualizado")

    def test_valid_post_redirects_to_detail(self):
        response = self._post_update(
            self.user,
            self._valid_data(trade_name="Norte Actualizado"),
        )

        self.assertRedirects(
            response,
            reverse("customers:customer_detail", args=[self.customer.pk]),
        )

    def test_missing_customer_returns_404(self):
        missing_url = reverse(
            "customers:customer_update",
            args=[self.customer.pk + 999],
        )
        self.client.force_login(self.user)
        response = self.client.get(missing_url)

        self.assertEqual(response.status_code, 404)

    def test_invalid_post_keeps_previous_data(self):
        original_name = self.customer.trade_name
        response = self._post_update(self.user, self._valid_data(trade_name=""))

        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.trade_name, original_name)

    def test_duplicate_customer_code_does_not_update_customer(self):
        Customer.objects.create(
            trade_name="Otro Cliente",
            customer_code="C-9999",
            code_system=Customer.CodeSystem.ARION,
        )
        original_code = self.customer.customer_code

        response = self._post_update(
            self.user,
            self._valid_data(customer_code="C-9999"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors["customer_code"])
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.customer_code, original_code)

    def test_edit_customer_button_requires_change_permission(self):
        detail_url = reverse("customers:customer_detail", args=[self.customer.pk])

        self.client.force_login(self.viewer)
        hidden = self.client.get(detail_url)
        self.assertNotContains(hidden, "Editar cliente")
        self.assertNotContains(hidden, f'href="{self.url}"')

        self.client.force_login(self.user)
        visible = self.client.get(detail_url)
        self.assertContains(visible, "Editar cliente")
        self.assertContains(visible, f'href="{self.url}"')
