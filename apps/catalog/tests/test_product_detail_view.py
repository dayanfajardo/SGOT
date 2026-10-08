from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory

User = get_user_model()


class ProductDetailViewTests(TestCase):
    def setUp(self):
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_product",
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

        self.camara = Product.objects.create(
            name="Cámara IP 4MP",
            product_code="1-1-225",
            reference="DS-2CD2143",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.cable = Product.objects.create(
            name="Cable UTP Cat6",
            product_code="1-5-20",
            category=ProductCategory.MATERIALS_ACCESSORIES,
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
            active=False,
        )

        self.url = reverse("catalog:product_detail", args=[self.camara.pk])
        self.historical_url = reverse(
            "catalog:product_detail",
            args=[self.cable.pk],
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

    def test_detail_uses_product_detail_template(self):
        response = self._get_detail(self.user)

        self.assertTemplateUsed(response, "catalog/product_detail.html")

    def test_detail_shows_human_labels(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.camara.name)
        self.assertContains(response, self.camara.product_code)
        self.assertContains(response, self.camara.reference)
        self.assertContains(response, self.camara.get_category_display())
        self.assertContains(response, self.camara.get_product_type_display())
        self.assertContains(response, self.camara.get_unit_display())
        self.assertNotContains(response, "EQUIPMENT")
        self.assertNotContains(response, "UNIT")
        self.assertNotContains(response, "True")
        self.assertNotContains(response, "False")

    def test_historical_product_shows_dash_for_empty_fields(self):
        response = self._get_detail(self.user, self.historical_url)

        self.assertContains(response, self.cable.name)
        self.assertContains(response, "—")
        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-inactive">Inactivo</span>',
            html=True,
        )

    def test_missing_product_returns_404(self):
        missing_url = reverse(
            "catalog:product_detail",
            args=[self.camara.pk + 999],
        )
        response = self._get_detail(self.user, missing_url)

        self.assertEqual(response.status_code, 404)

    def test_list_links_name_to_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:product_list"))

        self.assertContains(
            response,
            f'<a href="{self.url}">{self.camara.name}</a>',
            html=True,
        )
