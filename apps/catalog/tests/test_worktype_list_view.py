from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import WorkType

User = get_user_model()


class WorkTypeListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:worktype_list")
        view_permission = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_worktype",
        )
        view_technician = Permission.objects.get(
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
        self.user_without_permission.user_permissions.add(view_technician)

        self.instalacion = WorkType.objects.create(
            name="Instalación de CCTV",
            description="Montaje e instalación de cámaras",
        )
        self.mantenimiento = WorkType.objects.create(
            name="Mantenimiento",
            description="Revisión periódica de equipos",
        )
        self.revision = WorkType.objects.create(
            name="Revisión de alarma",
            description="Diagnóstico de sistemas de alarma",
        )
        self.soporte = WorkType.objects.create(
            name="Soporte técnico",
            description="",
            active=False,
        )

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _worktypes(self, response):
        return list(response.context["worktypes"])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_user_with_view_permission_gets_200(self):
        response = self._get_list(self.user)

        self.assertEqual(response.status_code, 200)

    def test_list_uses_worktype_list_template(self):
        response = self._get_list(self.user)

        self.assertTemplateUsed(response, "catalog/worktype_list.html")

    def test_list_shows_existing_worktypes(self):
        response = self._get_list(self.user)

        self.assertEqual(
            self._worktypes(response),
            [self.instalacion, self.mantenimiento, self.revision, self.soporte],
        )
        self.assertContains(response, "Instalación de CCTV")
        self.assertContains(response, "Mantenimiento")
        self.assertContains(response, "Revisión de alarma")
        self.assertContains(response, "Soporte técnico")

    def test_search_by_name(self):
        response = self._get_list(self.user, {"q": "mantenimiento"})

        self.assertEqual(self._worktypes(response), [self.mantenimiento])

    def test_search_is_partial_and_case_insensitive(self):
        response = self._get_list(self.user, {"q": "CCTV"})

        self.assertEqual(self._worktypes(response), [self.instalacion])

    def test_search_by_description(self):
        response = self._get_list(self.user, {"q": "cámaras"})

        self.assertEqual(self._worktypes(response), [self.instalacion])

    def test_filter_active(self):
        response = self._get_list(self.user, {"active": "1"})

        self.assertEqual(
            self._worktypes(response),
            [self.instalacion, self.mantenimiento, self.revision],
        )

    def test_filter_inactive(self):
        response = self._get_list(self.user, {"active": "0"})

        self.assertEqual(self._worktypes(response), [self.soporte])

    def test_combined_search_and_active_filter(self):
        response = self._get_list(
            self.user,
            {
                "q": "soporte",
                "active": "0",
            },
        )

        self.assertEqual(self._worktypes(response), [self.soporte])

    def test_has_worktypes_is_false_when_catalog_is_empty(self):
        WorkType.objects.all().delete()

        response = self._get_list(self.user)

        self.assertFalse(response.context["has_worktypes"])
        self.assertEqual(self._worktypes(response), [])
        self.assertContains(response, "No hay tipos de trabajo registrados.")

    def test_has_worktypes_is_true_when_filters_have_no_matches(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertTrue(response.context["has_worktypes"])
        self.assertEqual(self._worktypes(response), [])
        self.assertContains(
            response,
            "No encontramos tipos de trabajo con los filtros seleccionados.",
        )

    def test_empty_description_shows_dash(self):
        response = self._get_list(self.user)

        self.assertContains(response, "—")
        self.assertContains(response, self.soporte.name)
        self.assertNotContains(response, "None")

    def test_list_shows_human_status_labels(self):
        response = self._get_list(self.user)

        self.assertContains(response, "Activo")
        self.assertContains(response, "Inactivo")
        self.assertNotContains(response, ">True<")
        self.assertNotContains(response, ">False<")

    def test_sidebar_link_appears_with_view_worktype(self):
        response = self._get_list(self.user)

        self.assertContains(response, "Tipos de trabajo")
        self.assertContains(response, f'href="{self.url}"')

    def test_sidebar_link_does_not_appear_without_view_worktype(self):
        self.client.force_login(self.user_without_permission)
        response = self.client.get(reverse("catalog:technician_list"))

        self.assertNotContains(response, f'href="{self.url}"')
        self.assertNotContains(response, ">Tipos de trabajo</a>")
