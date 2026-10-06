from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.customers.models import Customer

User = get_user_model()


class CustomerListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("customers:customer_list")
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
            email="contacto@alarmasdelnorte.test",
        )
        self.acme = Customer.objects.create(
            customer_code="ACM-01",
            code_system=Customer.CodeSystem.ARION,
            trade_name="Acme Seguridad",
            legal_name="Acme Seguridad Ltda.",
            document="800987654-2",
            email="ventas@acme.test",
        )

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _customers(self, response):
        return list(response.context["customers"])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_user_with_view_permission_gets_200(self):
        response = self._get_list(self.user)

        self.assertEqual(response.status_code, 200)

    def test_list_uses_customer_list_template(self):
        response = self._get_list(self.user)

        self.assertTemplateUsed(response, "customers/customer_list.html")

    def test_filter_form_is_in_context(self):
        response = self._get_list(self.user)

        self.assertIn("filter_form", response.context)

    def test_list_is_ordered_by_trade_name(self):
        response = self._get_list(self.user)

        self.assertEqual(self._customers(response), [self.acme, self.norte])

    def test_search_by_trade_name(self):
        response = self._get_list(self.user, {"q": "acme seguridad"})

        self.assertEqual(self._customers(response), [self.acme])

    def test_search_by_legal_name(self):
        response = self._get_list(self.user, {"q": "norte s.a.s"})

        self.assertEqual(self._customers(response), [self.norte])

    def test_search_by_document(self):
        response = self._get_list(self.user, {"q": "800987654"})

        self.assertEqual(self._customers(response), [self.acme])

    def test_search_by_customer_code(self):
        response = self._get_list(self.user, {"q": "c-1001"})

        self.assertEqual(self._customers(response), [self.norte])

    def test_search_by_email(self):
        response = self._get_list(self.user, {"q": "ventas@acme"})

        self.assertEqual(self._customers(response), [self.acme])

    def test_search_is_partial_and_case_insensitive(self):
        response = self._get_list(self.user, {"q": "ALARMAS"})

        self.assertEqual(self._customers(response), [self.norte])

    def test_filter_by_code_system_centurion(self):
        response = self._get_list(
            self.user,
            {"code_system": Customer.CodeSystem.CENTURION},
        )

        self.assertEqual(self._customers(response), [self.norte])

    def test_filter_by_code_system_arion(self):
        response = self._get_list(
            self.user,
            {"code_system": Customer.CodeSystem.ARION},
        )

        self.assertEqual(self._customers(response), [self.acme])

    def test_combined_search_and_code_system_filter(self):
        response = self._get_list(
            self.user,
            {
                "q": "seguridad",
                "code_system": Customer.CodeSystem.ARION,
            },
        )

        self.assertEqual(self._customers(response), [self.acme])

    def test_filters_without_matches_return_empty_queryset(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertEqual(self._customers(response), [])

    def test_has_customers_is_false_when_catalog_is_empty(self):
        Customer.objects.all().delete()

        response = self._get_list(self.user)

        self.assertFalse(response.context["has_customers"])
        self.assertEqual(self._customers(response), [])

    def test_has_customers_is_true_when_filters_have_no_matches(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertTrue(response.context["has_customers"])
        self.assertEqual(self._customers(response), [])
