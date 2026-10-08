from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory

User = get_user_model()


class ProductToggleActiveViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="change_product",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_product",
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

        self.product = Product.objects.create(
            name="Cámara IP 4MP",
            product_code="1-1-1",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.url = reverse(
            "catalog:product_toggle_active",
            args=[self.product.pk],
        )
        self.detail_url = reverse(
            "catalog:product_detail",
            args=[self.product.pk],
        )

    def _post_toggle(self, user, url=None):
        self.client.force_login(user)
        return self.client.post(url or self.url)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._post_toggle(self.user_without_permission)

        self.assertEqual(response.status_code, 403)
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)

    def test_get_does_not_change_active_state(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.product.refresh_from_db()
        self.assertTrue(self.product.active)

    def test_post_deactivates_active_product(self):
        self._post_toggle(self.user)

        self.product.refresh_from_db()
        self.assertFalse(self.product.active)

    def test_post_activates_inactive_product(self):
        self.product.active = False
        self.product.save(update_fields=["active"])

        self._post_toggle(self.user)

        self.product.refresh_from_db()
        self.assertTrue(self.product.active)

    def test_missing_product_returns_404(self):
        missing_url = reverse(
            "catalog:product_toggle_active",
            args=[self.product.pk + 999],
        )
        response = self._post_toggle(self.user, missing_url)

        self.assertEqual(response.status_code, 404)

    def test_post_redirects_to_detail(self):
        response = self._post_toggle(self.user)

        self.assertRedirects(response, self.detail_url)

    def test_user_with_change_permission_sees_deactivate_action(self):
        self.client.force_login(self.user)
        response = self.client.get(self.detail_url)

        self.assertContains(
            response,
            '<button type="submit" class="sgot-btn sgot-btn-danger">Desactivar</button>',
            html=True,
        )
        self.assertContains(response, f'action="{self.url}"')
        self.assertNotContains(
            response,
            '<button type="submit" class="sgot-btn sgot-btn-secondary">Activar</button>',
            html=True,
        )

    def test_user_with_change_permission_sees_activate_action(self):
        self.product.active = False
        self.product.save(update_fields=["active"])

        self.client.force_login(self.user)
        response = self.client.get(self.detail_url)

        self.assertContains(
            response,
            '<button type="submit" class="sgot-btn sgot-btn-secondary">Activar</button>',
            html=True,
        )
        self.assertContains(response, f'action="{self.url}"')
        self.assertNotContains(
            response,
            '<button type="submit" class="sgot-btn sgot-btn-danger">Desactivar</button>',
            html=True,
        )

    def test_user_without_change_permission_does_not_see_action(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url)

        self.assertNotContains(response, "Desactivar")
        self.assertNotContains(response, "Activar")
        self.assertNotContains(response, f'action="{self.url}"')
