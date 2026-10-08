from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Product, ProductCategory

User = get_user_model()


class ProductCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:product_create")
        add_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="add_product",
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
            "product_code": "1-1-225",
            "name": "Cámara IP 4MP",
            "reference": "DS-2CD2143",
            "category": ProductCategory.CCTV,
            "product_type": Product.ProductType.EQUIPMENT,
            "unit": Product.Unit.UNIT,
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

    def test_valid_post_creates_product(self):
        self._post_create(self.user)

        product = Product.objects.get(product_code="1-1-225")
        self.assertEqual(product.name, "Cámara IP 4MP")
        self.assertEqual(product.reference, "DS-2CD2143")
        self.assertEqual(product.category, ProductCategory.CCTV)
        self.assertEqual(product.product_type, Product.ProductType.EQUIPMENT)
        self.assertEqual(product.unit, Product.Unit.UNIT)
        self.assertTrue(product.active)

    def test_valid_post_redirects_to_detail(self):
        response = self._post_create(self.user)
        product = Product.objects.get(product_code="1-1-225")

        self.assertRedirects(
            response,
            reverse("catalog:product_detail", args=[product.pk]),
        )

    def test_new_product_requires_code_and_category(self):
        response = self._post_create(
            self.user,
            self._valid_data(product_code="", category=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertTrue(response.context["form"].errors["product_code"])
        self.assertTrue(response.context["form"].errors["category"])

    def test_duplicate_product_code_does_not_create_product(self):
        Product.objects.create(
            name="Cámara existente",
            product_code="1-1-225",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )

        response = self._post_create(self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(response.context["form"].errors["product_code"])

    def test_mismatched_category_does_not_create_product(self):
        response = self._post_create(
            self.user,
            self._valid_data(category=ProductCategory.INTRUSION),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertTrue(response.context["form"].errors["category"])

    def test_materials_code_with_equipment_does_not_create_product(self):
        response = self._post_create(
            self.user,
            self._valid_data(
                product_code="1-5-12",
                category=ProductCategory.MATERIALS_ACCESSORIES,
                product_type=Product.ProductType.EQUIPMENT,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)
        self.assertTrue(response.context["form"].errors["product_type"])

    def test_new_product_button_requires_add_permission(self):
        list_url = reverse("catalog:product_list")
        create_url = reverse("catalog:product_create")

        self.client.force_login(self.viewer)
        hidden = self.client.get(list_url)
        self.assertNotContains(hidden, "Nuevo producto")
        self.assertNotContains(hidden, f'href="{create_url}"')

        self.client.force_login(self.user)
        visible = self.client.get(list_url)
        self.assertContains(visible, "Nuevo producto")
        self.assertContains(visible, f'href="{create_url}"')


class ProductUpdateViewTests(TestCase):
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
            product_code="1-1-225",
            reference="DS-2CD2143",
            category=ProductCategory.CCTV,
            product_type=Product.ProductType.EQUIPMENT,
            unit=Product.Unit.UNIT,
        )
        self.historical = Product.objects.create(
            name="Cable UTP Cat6",
            product_code="1-5-12",
            reference="1-1-99",
            category=ProductCategory.MATERIALS_ACCESSORIES,
            product_type=Product.ProductType.MATERIAL,
            unit=Product.Unit.METER,
        )
        self.url = reverse("catalog:product_update", args=[self.product.pk])
        self.historical_url = reverse(
            "catalog:product_update",
            args=[self.historical.pk],
        )

    def _valid_data(self, product=None, **overrides):
        product = product or self.product
        data = {
            "product_code": product.product_code or "",
            "name": product.name,
            "reference": product.reference,
            "category": product.category or "",
            "product_type": product.product_type,
            "unit": product.unit,
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

    def test_valid_post_updates_product(self):
        self._post_update(
            self.user,
            self._valid_data(name="Cámara IP 8MP", reference="DS-2CD2185"),
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Cámara IP 8MP")
        self.assertEqual(self.product.reference, "DS-2CD2185")
        self.assertEqual(self.product.product_code, "1-1-225")

    def test_valid_post_redirects_to_detail(self):
        response = self._post_update(
            self.user,
            self._valid_data(name="Cámara IP 8MP"),
        )

        self.assertRedirects(
            response,
            reverse("catalog:product_detail", args=[self.product.pk]),
        )

    def test_product_can_be_edited_keeping_code_and_category(self):
        self.client.force_login(self.user)
        get_response = self.client.get(self.historical_url)
        self.assertEqual(get_response.status_code, 200)

        response = self._post_update(
            self.user,
            self._valid_data(
                self.historical,
                name="Cable UTP Cat6 exterior",
            ),
            url=self.historical_url,
        )

        self.assertRedirects(
            response,
            reverse("catalog:product_detail", args=[self.historical.pk]),
        )
        self.historical.refresh_from_db()
        self.assertEqual(self.historical.name, "Cable UTP Cat6 exterior")
        self.assertEqual(self.historical.product_code, "1-5-12")
        self.assertEqual(
            self.historical.category,
            ProductCategory.MATERIALS_ACCESSORIES,
        )
        self.assertEqual(self.historical.reference, "1-1-99")

    def test_product_can_update_code_category_and_reference(self):
        response = self._post_update(
            self.user,
            self._valid_data(
                self.historical,
                product_code="1-5-40",
                reference="UTP-CAT6",
                category=ProductCategory.MATERIALS_ACCESSORIES,
            ),
            url=self.historical_url,
        )

        self.assertRedirects(
            response,
            reverse("catalog:product_detail", args=[self.historical.pk]),
        )
        self.historical.refresh_from_db()
        self.assertEqual(self.historical.product_code, "1-5-40")
        self.assertEqual(
            self.historical.category,
            ProductCategory.MATERIALS_ACCESSORIES,
        )
        self.assertEqual(self.historical.reference, "UTP-CAT6")

    def test_mismatched_category_does_not_update_product(self):
        original_category = self.product.category
        response = self._post_update(
            self.user,
            self._valid_data(category=ProductCategory.INTRUSION),
        )

        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.category, original_category)
        self.assertTrue(response.context["form"].errors["category"])

    def test_edit_product_button_requires_change_permission(self):
        detail_url = reverse("catalog:product_detail", args=[self.product.pk])

        self.client.force_login(self.viewer)
        hidden = self.client.get(detail_url)
        self.assertNotContains(hidden, "Editar producto")
        self.assertNotContains(hidden, f'href="{self.url}"')

        self.client.force_login(self.user)
        visible = self.client.get(detail_url)
        self.assertContains(visible, "Editar producto")
        self.assertContains(visible, f'href="{self.url}"')
