from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory

User = get_user_model()


class ProductListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:product_list")
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

        self.alarma = Product.objects.create(
            name="Alarma perimetral",
            product_code="2-1-20",
            reference="PARADOX-SP",
            category=ProductCategory.INTRUSION,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.cable = Product.objects.create(
            name="Cable UTP Cat6",
            product_code="1-5-20",
            reference="UTP-CAT6",
            category=ProductCategory.MATERIALS_ACCESSORIES,
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )
        self.camara = Product.objects.create(
            name="Cámara IP 4MP",
            product_code="1-1-225",
            reference="DS-2CD2143",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.conector = Product.objects.create(
            name="Conector BNC",
            product_code="1-5-12",
            category=ProductCategory.MATERIALS_ACCESSORIES,
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.UNIT,
            active=False,
        )

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _products(self, response):
        return list(response.context["products"])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_user_with_view_permission_gets_200(self):
        response = self._get_list(self.user)

        self.assertEqual(response.status_code, 200)

    def test_list_uses_product_list_template(self):
        response = self._get_list(self.user)

        self.assertTemplateUsed(response, "catalog/product_list.html")

    def test_list_shows_existing_products(self):
        response = self._get_list(self.user)

        self.assertEqual(
            self._products(response),
            list(Product.objects.all()),
        )
        self.assertContains(response, "Alarma perimetral")
        self.assertContains(response, "Cable UTP Cat6")
        self.assertContains(response, "Cámara IP 4MP")
        self.assertContains(response, "Conector BNC")

    def test_search_by_product_code(self):
        response = self._get_list(self.user, {"q": "1-1-225"})

        self.assertEqual(self._products(response), [self.camara])

    def test_search_by_name(self):
        response = self._get_list(self.user, {"q": "alarma"})

        self.assertEqual(self._products(response), [self.alarma])

    def test_search_by_reference(self):
        response = self._get_list(self.user, {"q": "UTP-CAT6"})

        self.assertEqual(self._products(response), [self.cable])

    def test_filter_by_category(self):
        response = self._get_list(
            self.user,
            {"category": ProductCategory.INTRUSION},
        )

        self.assertEqual(self._products(response), [self.alarma])

    def test_filter_by_product_type(self):
        response = self._get_list(
            self.user,
            {"product_type": Product.ProductType.MATERIAL},
        )

        self.assertEqual(self._products(response), [self.cable, self.conector])

    def test_filter_by_active_status(self):
        response = self._get_list(self.user, {"active": "0"})

        self.assertEqual(self._products(response), [self.conector])

    def test_combined_filters(self):
        response = self._get_list(
            self.user,
            {
                "q": "conector",
                "category": ProductCategory.MATERIALS_ACCESSORIES,
                "product_type": Product.ProductType.MATERIAL,
                "active": "0",
            },
        )

        self.assertEqual(self._products(response), [self.conector])

    def test_list_shows_human_labels(self):
        response = self._get_list(self.user)

        self.assertContains(response, "Intrusión")
        self.assertContains(response, "CCTV")
        self.assertContains(response, "Materiales y accesorios")
        self.assertContains(response, "Equipo")
        self.assertContains(response, "Material")
        self.assertContains(response, "Unidad")
        self.assertContains(response, "Metro")

    def test_empty_reference_shows_dash(self):
        response = self._get_list(self.user)

        self.assertContains(response, "—")
        self.assertContains(response, self.conector.name)
        self.assertNotContains(response, "None")

    def test_has_products_is_false_when_catalog_is_empty(self):
        Product.objects.all().delete()

        response = self._get_list(self.user)

        self.assertFalse(response.context["has_products"])
        self.assertEqual(self._products(response), [])

    def test_has_products_is_true_when_filters_have_no_matches(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertTrue(response.context["has_products"])
        self.assertEqual(self._products(response), [])
