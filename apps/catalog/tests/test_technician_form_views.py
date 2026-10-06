from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Technician

User = get_user_model()


class TechnicianCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:technician_create")
        add_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="add_technician",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_technician",
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
            "first_name": "Laura",
            "last_name": "Castro",
            "phone": "3110001122",
            "technician_type": Technician.TechnicianType.STAFF,
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

    def test_valid_post_creates_technician(self):
        self._post_create(self.user)

        technician = Technician.objects.get(first_name="Laura", last_name="Castro")
        self.assertEqual(technician.phone, "3110001122")
        self.assertEqual(
            technician.technician_type,
            Technician.TechnicianType.STAFF,
        )
        self.assertTrue(technician.active)

    def test_valid_post_redirects_to_detail(self):
        response = self._post_create(self.user)
        technician = Technician.objects.get(first_name="Laura", last_name="Castro")

        self.assertRedirects(
            response,
            reverse("catalog:technician_detail", args=[technician.pk]),
        )

    def test_invalid_post_does_not_create_technician(self):
        response = self._post_create(self.user, self._valid_data(first_name=""))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Technician.objects.count(), 0)

    def test_new_technician_button_requires_add_permission(self):
        list_url = reverse("catalog:technician_list")
        create_url = reverse("catalog:technician_create")

        self.client.force_login(self.viewer)
        hidden = self.client.get(list_url)
        self.assertNotContains(hidden, "Nuevo técnico")
        self.assertNotContains(hidden, f'href="{create_url}"')

        self.client.force_login(self.user)
        visible = self.client.get(list_url)
        self.assertContains(visible, "Nuevo técnico")
        self.assertContains(visible, f'href="{create_url}"')


class TechnicianUpdateViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="change_technician",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_technician",
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

        self.technician = Technician.objects.create(
            first_name="Ana",
            last_name="Díaz",
            phone="3101234567",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.url = reverse(
            "catalog:technician_update",
            args=[self.technician.pk],
        )

    def _valid_data(self, **overrides):
        data = {
            "first_name": self.technician.first_name,
            "last_name": self.technician.last_name,
            "phone": self.technician.phone,
            "technician_type": self.technician.technician_type,
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

    def test_valid_post_updates_technician(self):
        self._post_update(
            self.user,
            self._valid_data(
                first_name="Ana María",
                technician_type=Technician.TechnicianType.CONTRACTOR,
            ),
        )

        self.technician.refresh_from_db()
        self.assertEqual(self.technician.first_name, "Ana María")
        self.assertEqual(
            self.technician.technician_type,
            Technician.TechnicianType.CONTRACTOR,
        )

    def test_valid_post_redirects_to_detail(self):
        response = self._post_update(
            self.user,
            self._valid_data(first_name="Ana María"),
        )

        self.assertRedirects(
            response,
            reverse("catalog:technician_detail", args=[self.technician.pk]),
        )

    def test_missing_technician_returns_404(self):
        missing_url = reverse(
            "catalog:technician_update",
            args=[self.technician.pk + 999],
        )
        self.client.force_login(self.user)
        response = self.client.get(missing_url)

        self.assertEqual(response.status_code, 404)

    def test_invalid_post_keeps_previous_data(self):
        original_name = self.technician.first_name
        response = self._post_update(self.user, self._valid_data(first_name=""))

        self.assertEqual(response.status_code, 200)
        self.technician.refresh_from_db()
        self.assertEqual(self.technician.first_name, original_name)

    def test_edit_technician_button_requires_change_permission(self):
        detail_url = reverse(
            "catalog:technician_detail",
            args=[self.technician.pk],
        )

        self.client.force_login(self.viewer)
        hidden = self.client.get(detail_url)
        self.assertNotContains(hidden, "Editar técnico")
        self.assertNotContains(hidden, f'href="{self.url}"')

        self.client.force_login(self.user)
        visible = self.client.get(detail_url)
        self.assertContains(visible, "Editar técnico")
        self.assertContains(visible, f'href="{self.url}"')
