from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import WorkType

User = get_user_model()


class WorkTypeDetailViewTests(TestCase):
    def setUp(self):
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_worktype",
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

        self.instalacion = WorkType.objects.create(
            name="Instalación de CCTV",
            description="Montaje e instalación de cámaras",
        )
        self.soporte = WorkType.objects.create(
            name="Soporte técnico",
            description="",
            active=False,
        )

        self.url = reverse("catalog:worktype_detail", args=[self.instalacion.pk])
        self.inactive_url = reverse(
            "catalog:worktype_detail",
            args=[self.soporte.pk],
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

    def test_detail_uses_worktype_detail_template(self):
        response = self._get_detail(self.user)

        self.assertTemplateUsed(response, "catalog/worktype_detail.html")

    def test_detail_shows_name(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.instalacion.name)

    def test_detail_shows_description(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.instalacion.description)

    def test_empty_description_shows_dash(self):
        response = self._get_detail(self.user, self.inactive_url)

        self.assertContains(response, self.soporte.name)
        self.assertContains(response, "—")
        self.assertNotContains(response, "None")

    def test_detail_shows_active_badge_for_active_worktype(self):
        response = self._get_detail(self.user)

        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-active">Activo</span>',
            html=True,
        )
        self.assertNotContains(response, "True")
        self.assertNotContains(response, "False")

    def test_detail_shows_inactive_badge_for_inactive_worktype(self):
        response = self._get_detail(self.user, self.inactive_url)

        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-inactive">Inactivo</span>',
            html=True,
        )
        self.assertNotContains(response, "True")
        self.assertNotContains(response, "False")

    def test_missing_worktype_returns_404(self):
        missing_url = reverse(
            "catalog:worktype_detail",
            args=[self.instalacion.pk + 999],
        )
        response = self._get_detail(self.user, missing_url)

        self.assertEqual(response.status_code, 404)

    def test_list_links_name_to_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:worktype_list"))

        self.assertContains(
            response,
            f'<a href="{self.url}">{self.instalacion.name}</a>',
            html=True,
        )
