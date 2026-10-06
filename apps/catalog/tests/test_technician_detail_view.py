from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Technician

User = get_user_model()


class TechnicianDetailViewTests(TestCase):
    def setUp(self):
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_technician",
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

        self.ana = Technician.objects.create(
            first_name="Ana",
            last_name="Díaz",
            phone="3101234567",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.pedro = Technician.objects.create(
            first_name="Pedro",
            last_name="López",
            phone="3001112233",
            technician_type=Technician.TechnicianType.CONTRACTOR,
            active=False,
        )

        self.url = reverse("catalog:technician_detail", args=[self.ana.pk])
        self.inactive_url = reverse(
            "catalog:technician_detail",
            args=[self.pedro.pk],
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

    def test_detail_uses_technician_detail_template(self):
        response = self._get_detail(self.user)

        self.assertTemplateUsed(response, "catalog/technician_detail.html")

    def test_detail_shows_name_phone_and_human_type_label(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.ana.first_name)
        self.assertContains(response, self.ana.last_name)
        self.assertContains(response, self.ana.phone)
        self.assertContains(response, self.ana.get_technician_type_display())
        self.assertNotContains(response, "STAFF")
        self.assertNotContains(response, "CONTRACTOR")
        self.assertNotContains(response, "True")
        self.assertNotContains(response, "False")

    def test_detail_shows_active_badge_for_active_technician(self):
        response = self._get_detail(self.user)

        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-active">Activo</span>',
            html=True,
        )

    def test_detail_shows_inactive_badge_for_inactive_technician(self):
        response = self._get_detail(self.user, self.inactive_url)

        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-inactive">Inactivo</span>',
            html=True,
        )

    def test_missing_technician_returns_404(self):
        missing_url = reverse(
            "catalog:technician_detail",
            args=[self.ana.pk + 999],
        )
        response = self._get_detail(self.user, missing_url)

        self.assertEqual(response.status_code, 404)

    def test_list_links_full_name_to_detail(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("catalog:technician_list"))

        self.assertContains(
            response,
            f'<a href="{self.url}">{self.ana}</a>',
            html=True,
        )
