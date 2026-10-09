from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import WorkType

User = get_user_model()


class WorkTypeCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:worktype_create")
        add_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="add_worktype",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_worktype",
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
            "name": "Instalación de CCTV",
            "description": "Montaje e instalación de cámaras",
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

    def test_valid_post_creates_worktype(self):
        self._post_create(self.user)

        worktype = WorkType.objects.get(name="Instalación de CCTV")
        self.assertEqual(worktype.description, "Montaje e instalación de cámaras")
        self.assertTrue(worktype.active)

    def test_valid_post_redirects_to_detail(self):
        response = self._post_create(self.user)
        worktype = WorkType.objects.get(name="Instalación de CCTV")

        self.assertRedirects(
            response,
            reverse("catalog:worktype_detail", args=[worktype.pk]),
        )

    def test_duplicate_name_does_not_create_worktype(self):
        WorkType.objects.create(name="Instalación de CCTV")

        response = self._post_create(self.user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkType.objects.filter(name="Instalación de CCTV").count(), 1)
        self.assertTrue(response.context["form"].errors["name"])

    def test_invalid_post_does_not_create_worktype(self):
        response = self._post_create(self.user, self._valid_data(name=""))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkType.objects.count(), 0)

    def test_new_worktype_button_requires_add_permission(self):
        list_url = reverse("catalog:worktype_list")
        create_url = reverse("catalog:worktype_create")

        self.client.force_login(self.viewer)
        hidden = self.client.get(list_url)
        self.assertNotContains(hidden, "Nuevo tipo de trabajo")
        self.assertNotContains(hidden, f'href="{create_url}"')

        self.client.force_login(self.user)
        visible = self.client.get(list_url)
        self.assertContains(visible, "Nuevo tipo de trabajo")
        self.assertContains(visible, f'href="{create_url}"')


class WorkTypeUpdateViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="change_worktype",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_worktype",
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

        self.worktype = WorkType.objects.create(
            name="Instalación de CCTV",
            description="Montaje e instalación de cámaras",
        )
        self.url = reverse(
            "catalog:worktype_update",
            args=[self.worktype.pk],
        )

    def _valid_data(self, **overrides):
        data = {
            "name": self.worktype.name,
            "description": self.worktype.description,
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

    def test_valid_post_updates_worktype(self):
        self._post_update(
            self.user,
            self._valid_data(
                name="Mantenimiento de CCTV",
                description="Revisión periódica de cámaras",
            ),
        )

        self.worktype.refresh_from_db()
        self.assertEqual(self.worktype.name, "Mantenimiento de CCTV")
        self.assertEqual(
            self.worktype.description,
            "Revisión periódica de cámaras",
        )

    def test_valid_post_redirects_to_detail(self):
        response = self._post_update(
            self.user,
            self._valid_data(name="Mantenimiento de CCTV"),
        )

        self.assertRedirects(
            response,
            reverse("catalog:worktype_detail", args=[self.worktype.pk]),
        )

    def test_missing_worktype_returns_404(self):
        missing_url = reverse(
            "catalog:worktype_update",
            args=[self.worktype.pk + 999],
        )
        self.client.force_login(self.user)
        response = self.client.get(missing_url)

        self.assertEqual(response.status_code, 404)

    def test_invalid_post_keeps_previous_data(self):
        original_name = self.worktype.name
        original_description = self.worktype.description
        response = self._post_update(self.user, self._valid_data(name=""))

        self.assertEqual(response.status_code, 200)
        self.worktype.refresh_from_db()
        self.assertEqual(self.worktype.name, original_name)
        self.assertEqual(self.worktype.description, original_description)

    def test_edit_worktype_button_requires_change_permission(self):
        detail_url = reverse(
            "catalog:worktype_detail",
            args=[self.worktype.pk],
        )

        self.client.force_login(self.viewer)
        hidden = self.client.get(detail_url)
        self.assertNotContains(hidden, "Editar")
        self.assertNotContains(hidden, f'href="{self.url}"')

        self.client.force_login(self.user)
        visible = self.client.get(detail_url)
        self.assertContains(visible, "Editar")
        self.assertContains(visible, f'href="{self.url}"')
