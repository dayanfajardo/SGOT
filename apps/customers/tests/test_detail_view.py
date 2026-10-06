from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.customers.models import Customer

User = get_user_model()


class CustomerDetailViewTests(TestCase):
    def setUp(self):
        view_permission = Permission.objects.get(
            content_type__app_label="customers",
            codename="view_customer",
        )

        self.user = User.objects.create_user(
            username="con.permiso",
            email="con.permiso@example.com",
            password="pass",
        )
        self.user.user_permissions.add(view_permission)
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.norte = Customer.objects.create(
            customer_code="C-1001",
            code_system=Customer.CodeSystem.CENTURION,
            trade_name="Alarmas del Norte",
            legal_name="Alarmas del Norte S.A.S.",
            document="900123456-1",
            phone="3001234567",
            email="contacto@alarmasdelnorte.test",
        )
        self.sin_datos = Customer.objects.create(trade_name="Cliente Sin Datos")

        self.url = reverse("customers:customer_detail", args=[self.norte.pk])
        self.empty_url = reverse(
            "customers:customer_detail",
            args=[self.sin_datos.pk],
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

    def test_user_with_view_permission_gets_200(self):
        response = self._get_detail(self.user)

        self.assertEqual(response.status_code, 200)

    def test_missing_customer_returns_404(self):
        missing_url = reverse("customers:customer_detail", args=[self.norte.pk + 999])
        response = self._get_detail(self.user, missing_url)

        self.assertEqual(response.status_code, 404)

    def test_detail_uses_customer_detail_template(self):
        response = self._get_detail(self.user)

        self.assertTemplateUsed(response, "customers/customer_detail.html")

    def test_detail_shows_trade_name(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.norte.trade_name)

    def test_detail_shows_legal_name(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.norte.legal_name)

    def test_detail_shows_document(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.norte.document)

    def test_detail_shows_customer_code_when_present(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.norte.customer_code)

    def test_detail_shows_human_code_system_label(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.norte.get_code_system_display())
        self.assertNotContains(response, "CENTURION")

    def test_empty_optional_values_render_as_dash(self):
        response = self._get_detail(self.user, self.empty_url)

        self.assertContains(response, "—")
        self.assertNotContains(response, "None")

    def test_list_links_trade_name_to_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("customers:customer_list"))

        self.assertContains(
            response,
            f'<a href="{self.url}">{self.norte.trade_name}</a>',
            html=True,
        )
