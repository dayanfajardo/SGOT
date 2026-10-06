from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.catalog.models import Technician

User = get_user_model()


class TechnicianListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("catalog:technician_list")
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
            phone="",
            technician_type=Technician.TechnicianType.CONTRACTOR,
            active=False,
        )
        self.carlos = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            phone="3001112233",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.marta = Technician.objects.create(
            first_name="Marta",
            last_name="Ruiz",
            phone="3159998877",
            technician_type=Technician.TechnicianType.CONTRACTOR,
        )

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _technicians(self, response):
        return list(response.context["technicians"])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_user_with_view_permission_gets_200(self):
        response = self._get_list(self.user)

        self.assertEqual(response.status_code, 200)

    def test_list_uses_technician_list_template(self):
        response = self._get_list(self.user)

        self.assertTemplateUsed(response, "catalog/technician_list.html")

    def test_list_shows_existing_technicians(self):
        response = self._get_list(self.user)

        self.assertEqual(
            self._technicians(response),
            [self.ana, self.carlos, self.marta, self.pedro],
        )
        self.assertContains(response, "Ana Díaz")
        self.assertContains(response, "Carlos Pérez")
        self.assertContains(response, "Marta Ruiz")
        self.assertContains(response, "Pedro López")

    def test_list_is_ordered_by_first_name_and_last_name(self):
        response = self._get_list(self.user)

        self.assertEqual(
            self._technicians(response),
            [self.ana, self.carlos, self.marta, self.pedro],
        )

    def test_search_by_first_name(self):
        response = self._get_list(self.user, {"q": "carlos"})

        self.assertEqual(self._technicians(response), [self.carlos])

    def test_search_is_partial_and_case_insensitive(self):
        response = self._get_list(self.user, {"q": "PÉREZ"})

        self.assertEqual(self._technicians(response), [self.carlos])

    def test_search_by_last_name(self):
        response = self._get_list(self.user, {"q": "díaz"})

        self.assertEqual(self._technicians(response), [self.ana])

    def test_search_by_phone(self):
        response = self._get_list(self.user, {"q": "300111"})

        self.assertEqual(self._technicians(response), [self.carlos])

    def test_search_without_results_returns_empty_queryset(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertEqual(self._technicians(response), [])

    def test_filter_by_technician_type_staff(self):
        response = self._get_list(
            self.user,
            {"technician_type": Technician.TechnicianType.STAFF},
        )

        self.assertEqual(self._technicians(response), [self.ana, self.carlos])

    def test_filter_by_technician_type_contractor(self):
        response = self._get_list(
            self.user,
            {"technician_type": Technician.TechnicianType.CONTRACTOR},
        )

        self.assertEqual(self._technicians(response), [self.marta, self.pedro])

    def test_filter_active(self):
        response = self._get_list(self.user, {"active": "1"})

        self.assertEqual(
            self._technicians(response),
            [self.ana, self.carlos, self.marta],
        )

    def test_filter_inactive(self):
        response = self._get_list(self.user, {"active": "0"})

        self.assertEqual(self._technicians(response), [self.pedro])

    def test_combined_type_and_active_filters(self):
        response = self._get_list(
            self.user,
            {
                "technician_type": Technician.TechnicianType.CONTRACTOR,
                "active": "1",
            },
        )

        self.assertEqual(self._technicians(response), [self.marta])

    def test_combined_search_and_filters(self):
        response = self._get_list(
            self.user,
            {
                "q": "ana",
                "technician_type": Technician.TechnicianType.STAFF,
                "active": "1",
            },
        )

        self.assertEqual(self._technicians(response), [self.ana])

    def test_has_technicians_is_false_when_catalog_is_empty(self):
        Technician.objects.all().delete()

        response = self._get_list(self.user)

        self.assertFalse(response.context["has_technicians"])
        self.assertEqual(self._technicians(response), [])

    def test_has_technicians_is_true_when_filters_have_no_matches(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertTrue(response.context["has_technicians"])
        self.assertEqual(self._technicians(response), [])
