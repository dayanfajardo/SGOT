from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.accounts.constants import (
    ADMIN_GROUP,
    COMMERCIAL_GROUP,
    DEFAULT_GROUPS,
    LEGACY_ADMIN_WAREHOUSE_GROUP,
    MANAGEMENT_GROUP,
    TECHNICAL_MANAGER_GROUP,
    WAREHOUSE_GROUP,
)

User = get_user_model()

OPERATIONAL_PERMISSIONS = {
    ("customers", "view_customer"),
    ("customers", "add_customer"),
    ("customers", "change_customer"),
    ("catalog", "view_product"),
    ("catalog", "add_product"),
    ("catalog", "change_product"),
    ("catalog", "view_technician"),
    ("catalog", "add_technician"),
    ("catalog", "change_technician"),
    ("catalog", "view_worktype"),
    ("catalog", "add_worktype"),
    ("catalog", "change_worktype"),
    ("workorders", "view_workorder"),
    ("workorders", "add_workorder"),
    ("workorders", "change_workorder"),
    ("workorders", "view_workorderitem"),
    ("workorders", "add_workorderitem"),
    ("workorders", "change_workorderitem"),
    ("workorders", "view_workorderhistory"),
    ("warehouse", "view_warehouseoutput"),
    ("warehouse", "add_warehouseoutput"),
    ("warehouse", "change_warehouseoutput"),
    ("warehouse", "view_warehouseoutputitem"),
    ("warehouse", "add_warehouseoutputitem"),
    ("warehouse", "change_warehouseoutputitem"),
}

ADMIN_USER_PERMISSIONS = {
    ("accounts", "view_user"),
    ("accounts", "add_user"),
    ("accounts", "change_user"),
}

COMMERCIAL_PERMISSIONS = {
    ("customers", "view_customer"),
    ("catalog", "view_product"),
    ("catalog", "view_worktype"),
    ("workorders", "view_workorder"),
    ("workorders", "view_workorderitem"),
}

TECHNICAL_MANAGER_PERMISSIONS = {
    ("customers", "view_customer"),
    ("catalog", "view_product"),
    ("catalog", "view_technician"),
    ("catalog", "view_worktype"),
    ("workorders", "view_workorder"),
    ("workorders", "view_workorderitem"),
    ("workorders", "schedule_workorder"),
}

MANAGEMENT_PERMISSIONS = {
    ("customers", "view_customer"),
    ("catalog", "view_product"),
    ("catalog", "view_technician"),
    ("catalog", "view_worktype"),
    ("workorders", "view_workorder"),
    ("workorders", "view_workorderitem"),
    ("workorders", "view_workorderhistory"),
    ("warehouse", "view_warehouseoutput"),
    ("warehouse", "view_warehouseoutputitem"),
}


def _permission_pairs(group):
    return set(
        group.permissions.values_list("content_type__app_label", "codename")
    )


class SetupRolesCommandTests(TestCase):
    def setUp(self):
        call_command("setup_roles")

    def test_creates_five_default_groups_without_legacy(self):
        self.assertEqual(
            DEFAULT_GROUPS,
            (
                ADMIN_GROUP,
                WAREHOUSE_GROUP,
                COMMERCIAL_GROUP,
                TECHNICAL_MANAGER_GROUP,
                MANAGEMENT_GROUP,
            ),
        )
        self.assertNotIn(LEGACY_ADMIN_WAREHOUSE_GROUP, DEFAULT_GROUPS)
        for group_name in DEFAULT_GROUPS:
            self.assertTrue(Group.objects.filter(name=group_name).exists())
        self.assertFalse(
            Group.objects.filter(name=LEGACY_ADMIN_WAREHOUSE_GROUP).exists()
        )

    def test_admin_has_current_operational_permissions(self):
        group = Group.objects.get(name=ADMIN_GROUP)

        self.assertTrue(OPERATIONAL_PERMISSIONS.issubset(_permission_pairs(group)))

    def test_warehouse_has_current_operational_permissions(self):
        group = Group.objects.get(name=WAREHOUSE_GROUP)

        self.assertEqual(_permission_pairs(group), OPERATIONAL_PERMISSIONS)

    def test_admin_has_user_management_permissions(self):
        group = Group.objects.get(name=ADMIN_GROUP)
        permissions = _permission_pairs(group)

        self.assertTrue(ADMIN_USER_PERMISSIONS.issubset(permissions))
        self.assertEqual(
            permissions,
            OPERATIONAL_PERMISSIONS | ADMIN_USER_PERMISSIONS,
        )

    def test_warehouse_does_not_have_user_management_permissions(self):
        group = Group.objects.get(name=WAREHOUSE_GROUP)
        permissions = _permission_pairs(group)

        for permission in ADMIN_USER_PERMISSIONS:
            self.assertNotIn(permission, permissions)

    def test_no_default_group_has_delete_user(self):
        for group_name in DEFAULT_GROUPS:
            group = Group.objects.get(name=group_name)
            self.assertNotIn(
                ("accounts", "delete_user"),
                _permission_pairs(group),
            )

    def test_commercial_keeps_current_permission_matrix(self):
        group = Group.objects.get(name=COMMERCIAL_GROUP)
        permissions = _permission_pairs(group)

        self.assertEqual(permissions, COMMERCIAL_PERMISSIONS)
        self.assertIn(("workorders", "view_workorder"), permissions)
        self.assertIn(("workorders", "view_workorderitem"), permissions)
        self.assertNotIn(("workorders", "add_workorder"), permissions)
        self.assertNotIn(("workorders", "add_workorderitem"), permissions)

    def test_warehouse_keeps_add_workorder_permissions(self):
        permissions = _permission_pairs(Group.objects.get(name=WAREHOUSE_GROUP))

        self.assertIn(("workorders", "add_workorder"), permissions)
        self.assertIn(("workorders", "add_workorderitem"), permissions)

    def test_admin_keeps_add_workorder_permissions(self):
        permissions = _permission_pairs(Group.objects.get(name=ADMIN_GROUP))

        self.assertIn(("workorders", "add_workorder"), permissions)
        self.assertIn(("workorders", "add_workorderitem"), permissions)

    def test_technical_manager_keeps_current_permission_matrix(self):
        group = Group.objects.get(name=TECHNICAL_MANAGER_GROUP)

        self.assertEqual(_permission_pairs(group), TECHNICAL_MANAGER_PERMISSIONS)

    def test_management_keeps_current_permission_matrix(self):
        group = Group.objects.get(name=MANAGEMENT_GROUP)

        self.assertEqual(_permission_pairs(group), MANAGEMENT_PERMISSIONS)

    def test_setup_roles_is_idempotent(self):
        first_permissions = {
            group_name: _permission_pairs(Group.objects.get(name=group_name))
            for group_name in DEFAULT_GROUPS
        }

        call_command("setup_roles")

        second_permissions = {
            group_name: _permission_pairs(Group.objects.get(name=group_name))
            for group_name in DEFAULT_GROUPS
        }

        self.assertEqual(first_permissions, second_permissions)
        self.assertEqual(
            Group.objects.filter(name__in=DEFAULT_GROUPS).count(),
            len(DEFAULT_GROUPS),
        )


class SetupRolesLegacyGroupTests(TestCase):
    def test_does_not_delete_or_reassign_legacy_group_users(self):
        legacy_group = Group.objects.create(name=LEGACY_ADMIN_WAREHOUSE_GROUP)
        marker_permission = Permission.objects.get(
            content_type__app_label="customers",
            codename="view_customer",
        )
        legacy_group.permissions.set([marker_permission])
        user = User.objects.create_user(
            username="legacy.admin",
            email="legacy.admin@example.com",
            password="pass",
        )
        user.groups.add(legacy_group)

        call_command("setup_roles")

        legacy_group.refresh_from_db()
        user.refresh_from_db()
        self.assertTrue(
            Group.objects.filter(name=LEGACY_ADMIN_WAREHOUSE_GROUP).exists()
        )
        self.assertEqual(
            _permission_pairs(legacy_group),
            {("customers", "view_customer")},
        )
        self.assertEqual(set(user.groups.all()), {legacy_group})


class TechnicalManagerCustomerPermissionTests(TestCase):
    def setUp(self):
        call_command("setup_roles")
        self.group = Group.objects.get(name=TECHNICAL_MANAGER_GROUP)

    def _has_customer_permission(self, codename):
        return self.group.permissions.filter(
            content_type__app_label="customers",
            codename=codename,
        ).exists()

    def test_technical_manager_has_view_customer(self):
        self.assertTrue(self._has_customer_permission("view_customer"))

    def test_technical_manager_does_not_have_add_customer(self):
        self.assertFalse(self._has_customer_permission("add_customer"))

    def test_technical_manager_does_not_have_change_customer(self):
        self.assertFalse(self._has_customer_permission("change_customer"))

    def test_technical_manager_does_not_have_delete_customer(self):
        self.assertFalse(self._has_customer_permission("delete_customer"))


class TechnicalManagerProductPermissionTests(TestCase):
    def setUp(self):
        call_command("setup_roles")
        self.group = Group.objects.get(name=TECHNICAL_MANAGER_GROUP)

    def _has_product_permission(self, codename):
        return self.group.permissions.filter(
            content_type__app_label="catalog",
            codename=codename,
        ).exists()

    def test_technical_manager_has_view_product(self):
        self.assertTrue(self._has_product_permission("view_product"))

    def test_technical_manager_does_not_have_add_product(self):
        self.assertFalse(self._has_product_permission("add_product"))

    def test_technical_manager_does_not_have_change_product(self):
        self.assertFalse(self._has_product_permission("change_product"))

    def test_technical_manager_does_not_have_delete_product(self):
        self.assertFalse(self._has_product_permission("delete_product"))


class ProductSidebarNavigationTests(TestCase):
    def setUp(self):
        self.products_url = reverse("catalog:product_list")
        self.technicians_url = reverse("catalog:technician_list")
        view_product = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_product",
        )
        view_technician = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_technician",
        )

        self.user_with_view_product = User.objects.create_user(
            username="con.productos",
            email="con.productos@example.com",
            password="pass",
        )
        self.user_with_view_product.user_permissions.add(view_product)
        self.user_without_view_product = User.objects.create_user(
            username="sin.productos",
            email="sin.productos@example.com",
            password="pass",
        )
        self.user_without_view_product.user_permissions.add(view_technician)

    def test_products_link_appears_with_view_product(self):
        self.client.force_login(self.user_with_view_product)
        response = self.client.get(self.products_url)

        self.assertContains(response, "Productos")
        self.assertContains(response, f'href="{self.products_url}"')

    def test_products_link_does_not_appear_without_view_product(self):
        self.client.force_login(self.user_without_view_product)
        response = self.client.get(self.technicians_url)

        self.assertNotContains(response, f'href="{self.products_url}"')
        self.assertNotContains(response, ">Productos</a>")


class UserListViewTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:user_list")
        view_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )
        view_technician = Permission.objects.get(
            content_type__app_label="catalog",
            codename="view_technician",
        )

        self.admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)
        self.warehouse_group, _ = Group.objects.get_or_create(name=WAREHOUSE_GROUP)
        self.commercial_group, _ = Group.objects.get_or_create(name=COMMERCIAL_GROUP)
        self.technical_group, _ = Group.objects.get_or_create(
            name=TECHNICAL_MANAGER_GROUP
        )
        self.management_group, _ = Group.objects.get_or_create(name=MANAGEMENT_GROUP)

        self.user = self._create_listed_user(
            username="visor.lista",
            first_name="Visor",
            last_name="Lista",
            email="visor.lista@example.com",
        )
        self.user.user_permissions.add(view_permission)
        self.user_without_permission = self._create_listed_user(
            username="sin.permiso",
            first_name="Sin",
            last_name="Permiso",
            email="sin.permiso@example.com",
        )
        self.user_without_permission.user_permissions.add(view_technician)

        self.ada = self._create_listed_user(
            username="ada.admin",
            first_name="Ada",
            last_name="Admin",
            email="ada.admin@example.com",
            group=self.admin_group,
        )
        self.bruno = self._create_listed_user(
            username="bruno.bodega",
            first_name="Bruno",
            last_name="Bodega",
            email="bruno.bodega@example.com",
            group=self.warehouse_group,
        )
        self.carla = self._create_listed_user(
            username="carla.comercial",
            first_name="Carla",
            last_name="Comercial",
            email="carla.comercial@example.com",
            group=self.commercial_group,
        )
        self.diego = self._create_listed_user(
            username="diego.tecnica",
            first_name="Diego",
            last_name="Tecnica",
            email="diego.tecnica@example.com",
            group=self.technical_group,
        )
        self.elena = self._create_listed_user(
            username="elena.gerencia",
            first_name="Elena",
            last_name="Gerencia",
            email="elena.gerencia@example.com",
            group=self.management_group,
        )
        self.felipe = self._create_listed_user(
            username="felipe.inactivo",
            first_name="Felipe",
            last_name="Inactivo",
            email="felipe.inactivo@example.com",
            group=self.warehouse_group,
            is_active=False,
        )

    def _create_listed_user(
        self,
        username,
        first_name,
        last_name,
        email,
        group=None,
        is_active=True,
    ):
        user = User.objects.create_user(
            username=username,
            email=email,
            password="pass",
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
        )
        if group is not None:
            user.groups.add(group)
        return user

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _users(self, response):
        return list(response.context["users"])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_user_with_view_permission_gets_200(self):
        response = self._get_list(self.user)

        self.assertEqual(response.status_code, 200)

    def test_list_uses_user_list_template(self):
        response = self._get_list(self.user)

        self.assertTemplateUsed(response, "accounts/user_list.html")

    def test_list_shows_existing_users(self):
        response = self._get_list(self.user)

        self.assertEqual(
            self._users(response),
            [
                self.ada,
                self.bruno,
                self.carla,
                self.diego,
                self.elena,
                self.felipe,
                self.user_without_permission,
                self.user,
            ],
        )
        self.assertContains(response, "ada.admin")
        self.assertContains(response, "Ada Admin")
        self.assertContains(response, "bruno.bodega")
        self.assertContains(response, "carla.comercial")
        self.assertContains(response, "diego.tecnica")
        self.assertContains(response, "elena.gerencia")
        self.assertContains(response, "felipe.inactivo")

    def test_search_by_username(self):
        response = self._get_list(self.user, {"q": "bruno.bodega"})

        self.assertEqual(self._users(response), [self.bruno])

    def test_search_by_first_name(self):
        response = self._get_list(self.user, {"q": "carla"})

        self.assertEqual(self._users(response), [self.carla])

    def test_search_by_last_name(self):
        response = self._get_list(self.user, {"q": "tecnica"})

        self.assertEqual(self._users(response), [self.diego])

    def test_search_by_email(self):
        response = self._get_list(self.user, {"q": "elena.gerencia@"})

        self.assertEqual(self._users(response), [self.elena])

    def test_filter_by_admin_role(self):
        response = self._get_list(self.user, {"role": ADMIN_GROUP})

        self.assertEqual(self._users(response), [self.ada])

    def test_filter_by_warehouse_role(self):
        response = self._get_list(self.user, {"role": WAREHOUSE_GROUP})

        self.assertEqual(self._users(response), [self.bruno, self.felipe])

    def test_filter_by_commercial_role(self):
        response = self._get_list(self.user, {"role": COMMERCIAL_GROUP})

        self.assertEqual(self._users(response), [self.carla])

    def test_filter_by_technical_manager_role(self):
        response = self._get_list(self.user, {"role": TECHNICAL_MANAGER_GROUP})

        self.assertEqual(self._users(response), [self.diego])

    def test_filter_by_management_role(self):
        response = self._get_list(self.user, {"role": MANAGEMENT_GROUP})

        self.assertEqual(self._users(response), [self.elena])

    def test_filter_active(self):
        response = self._get_list(self.user, {"active": "1"})

        self.assertEqual(
            self._users(response),
            [
                self.ada,
                self.bruno,
                self.carla,
                self.diego,
                self.elena,
                self.user_without_permission,
                self.user,
            ],
        )

    def test_filter_inactive(self):
        response = self._get_list(self.user, {"active": "0"})

        self.assertEqual(self._users(response), [self.felipe])

    def test_combined_search_role_and_active_filters(self):
        response = self._get_list(
            self.user,
            {
                "q": "bruno",
                "role": WAREHOUSE_GROUP,
                "active": "1",
            },
        )

        self.assertEqual(self._users(response), [self.bruno])

    def test_has_users_is_false_when_there_are_no_users(self):
        with patch.object(
            User.objects,
            "prefetch_related",
            return_value=User.objects.none(),
        ):
            response = self._get_list(self.user)

        self.assertFalse(response.context["has_users"])
        self.assertEqual(self._users(response), [])
        self.assertContains(response, "No hay usuarios registrados.")

    def test_has_users_is_true_when_filters_have_no_matches(self):
        response = self._get_list(self.user, {"q": "ZZZ-NO-MATCH"})

        self.assertTrue(response.context["has_users"])
        self.assertEqual(self._users(response), [])
        self.assertContains(
            response,
            "No encontramos usuarios con los filtros seleccionados.",
        )

    def test_list_shows_human_status_and_role_labels(self):
        response = self._get_list(self.user)

        self.assertContains(response, "Activo")
        self.assertContains(response, "Inactivo")
        self.assertContains(response, ADMIN_GROUP)
        self.assertContains(response, WAREHOUSE_GROUP)
        self.assertNotContains(response, ">True<")
        self.assertNotContains(response, ">False<")

    def test_sidebar_link_appears_with_view_user(self):
        response = self._get_list(self.user)

        self.assertContains(response, "Usuarios")
        self.assertContains(response, f'href="{self.url}"')

    def test_sidebar_link_does_not_appear_without_view_user(self):
        self.client.force_login(self.user_without_permission)
        response = self.client.get(reverse("catalog:technician_list"))

        self.assertNotContains(response, f'href="{self.url}"')
        self.assertNotContains(response, ">Usuarios</a>")

    def test_list_links_username_to_detail(self):
        response = self._get_list(self.user)
        detail_url = reverse("accounts:user_detail", args=[self.bruno.pk])

        self.assertContains(
            response,
            f'<a href="{detail_url}">{self.bruno.username}</a>',
            html=True,
        )


class UserDetailViewTests(TestCase):
    def setUp(self):
        view_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )
        self.warehouse_group, _ = Group.objects.get_or_create(name=WAREHOUSE_GROUP)

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

        self.bruno = User.objects.create_user(
            username="bruno.bodega",
            email="bruno.bodega@example.com",
            password="pass",
            first_name="Bruno",
            last_name="Bodega",
        )
        self.bruno.groups.add(self.warehouse_group)
        self.felipe = User.objects.create_user(
            username="felipe.inactivo",
            email="felipe.inactivo@example.com",
            password="pass",
            first_name="Felipe",
            last_name="Inactivo",
            is_active=False,
        )

        self.url = reverse("accounts:user_detail", args=[self.bruno.pk])
        self.inactive_url = reverse(
            "accounts:user_detail",
            args=[self.felipe.pk],
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

    def test_detail_uses_user_detail_template(self):
        response = self._get_detail(self.user)

        self.assertTemplateUsed(response, "accounts/user_detail.html")

    def test_detail_shows_username(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.bruno.username)

    def test_detail_shows_first_and_last_name(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.bruno.first_name)
        self.assertContains(response, self.bruno.last_name)

    def test_detail_shows_email(self):
        response = self._get_detail(self.user)

        self.assertContains(response, self.bruno.email)

    def test_detail_shows_role(self):
        response = self._get_detail(self.user)

        self.assertContains(response, WAREHOUSE_GROUP)

    def test_detail_shows_active_badge_for_active_user(self):
        response = self._get_detail(self.user)

        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-active">Activo</span>',
            html=True,
        )

    def test_detail_shows_inactive_badge_for_inactive_user(self):
        response = self._get_detail(self.user, self.inactive_url)

        self.assertContains(
            response,
            '<span class="sgot-badge sgot-badge-inactive">Inactivo</span>',
            html=True,
        )

    def test_missing_user_returns_404(self):
        missing_url = reverse(
            "accounts:user_detail",
            args=[self.bruno.pk + 999],
        )
        response = self._get_detail(self.user, missing_url)

        self.assertEqual(response.status_code, 404)


class UserCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:user_create")
        add_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="add_user",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )

        for group_name in DEFAULT_GROUPS:
            Group.objects.get_or_create(name=group_name)

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
            "username": "nuevo.almacen",
            "first_name": "Nora",
            "last_name": "Almacén",
            "email": "nora.almacen@example.com",
            "role": WAREHOUSE_GROUP,
            "password1": "SgotInicial123",
            "password2": "SgotInicial123",
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

    def test_valid_post_creates_user(self):
        self._post_create(self.user)

        created = User.objects.get(username="nuevo.almacen")
        self.assertEqual(created.first_name, "Nora")
        self.assertEqual(created.last_name, "Almacén")
        self.assertEqual(created.email, "nora.almacen@example.com")

    def test_password_is_hashed_and_check_password_succeeds(self):
        self._post_create(self.user)

        created = User.objects.get(username="nuevo.almacen")
        self.assertNotEqual(created.password, "SgotInicial123")
        self.assertTrue(created.check_password("SgotInicial123"))

    def test_assigns_exactly_the_selected_role(self):
        self._post_create(self.user)

        created = User.objects.get(username="nuevo.almacen")
        self.assertEqual(
            list(created.groups.values_list("name", flat=True)),
            [WAREHOUSE_GROUP],
        )

    def test_created_user_is_active(self):
        self._post_create(self.user)

        created = User.objects.get(username="nuevo.almacen")
        self.assertTrue(created.is_active)

    def test_created_user_is_not_staff(self):
        self._post_create(self.user)

        created = User.objects.get(username="nuevo.almacen")
        self.assertFalse(created.is_staff)

    def test_created_user_is_not_superuser(self):
        self._post_create(self.user)

        created = User.objects.get(username="nuevo.almacen")
        self.assertFalse(created.is_superuser)

    def test_valid_post_redirects_to_detail(self):
        response = self._post_create(self.user)
        created = User.objects.get(username="nuevo.almacen")

        self.assertRedirects(
            response,
            reverse("accounts:user_detail", args=[created.pk]),
        )

    def test_mismatched_passwords_do_not_create_user(self):
        response = self._post_create(
            self.user,
            self._valid_data(password2="OtraClave123"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nuevo.almacen").exists())

    def test_duplicate_username_does_not_create_user(self):
        response = self._post_create(
            self.user,
            self._valid_data(username=self.user.username),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username=self.user.username).count(), 1)

    def test_duplicate_email_does_not_create_user(self):
        response = self._post_create(
            self.user,
            self._valid_data(email=self.user.email),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nuevo.almacen").exists())
        self.assertEqual(
            User.objects.filter(email=self.user.email).count(),
            1,
        )

    def test_multiple_users_can_have_empty_email(self):
        self._post_create(
            self.user,
            self._valid_data(
                username="vacio.uno",
                email="",
            ),
        )
        self._post_create(
            self.user,
            self._valid_data(
                username="vacio.dos",
                email="",
            ),
        )

        self.assertEqual(
            User.objects.filter(
                username__in=["vacio.uno", "vacio.dos"],
                email__isnull=True,
            ).count(),
            2,
        )

    def test_legacy_role_cannot_be_selected(self):
        response = self._post_create(
            self.user,
            self._valid_data(role=LEGACY_ADMIN_WAREHOUSE_GROUP),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="nuevo.almacen").exists())
        self.assertIn("role", response.context["form"].errors)

    def test_new_user_button_requires_add_permission(self):
        list_url = reverse("accounts:user_list")
        create_url = reverse("accounts:user_create")

        self.client.force_login(self.viewer)
        hidden = self.client.get(list_url)
        self.assertNotContains(hidden, "Nuevo usuario")
        self.assertNotContains(hidden, f'href="{create_url}"')

        self.client.force_login(self.user)
        visible = self.client.get(list_url)
        self.assertContains(visible, "Nuevo usuario")
        self.assertContains(visible, f'href="{create_url}"')

    def test_password_help_renders_in_spanish(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertContains(response, "Su contraseña")
        self.assertNotContains(response, "Your password")


class UserUpdateViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="change_user",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )

        for group_name in DEFAULT_GROUPS:
            Group.objects.get_or_create(name=group_name)
        self.admin_group = Group.objects.get(name=ADMIN_GROUP)
        self.commercial_group = Group.objects.get(name=COMMERCIAL_GROUP)
        self.management_group = Group.objects.get(name=MANAGEMENT_GROUP)
        self.warehouse_group = Group.objects.get(name=WAREHOUSE_GROUP)

        self.user = User.objects.create_user(
            username="admin.editor",
            email="admin.editor@example.com",
            password="pass",
            first_name="Ada",
            last_name="Editor",
        )
        self.user.user_permissions.add(change_permission, view_permission)
        self.user.groups.set([self.admin_group])

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

        self.managed_user = User.objects.create_user(
            username="carla.comercial",
            email="carla.comercial@example.com",
            password="pass",
            first_name="Carla",
            last_name="Comercial",
        )
        self.managed_user.groups.set([self.commercial_group])
        self.other_user = User.objects.create_user(
            username="otro.usuario",
            email="otro.usuario@example.com",
            password="pass",
        )

        self.url = reverse(
            "accounts:user_update",
            args=[self.managed_user.pk],
        )
        self.self_url = reverse("accounts:user_update", args=[self.user.pk])

    def _valid_data(self, user=None, **overrides):
        target = user or self.managed_user
        data = {
            "username": target.username,
            "first_name": target.first_name,
            "last_name": target.last_name,
            "email": target.email or "",
            "role": (
                ADMIN_GROUP
                if target.pk == self.user.pk
                else COMMERCIAL_GROUP
            ),
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

    def test_edit_username(self):
        self._post_update(self.user, self._valid_data(username="carla.campo"))

        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.username, "carla.campo")

    def test_username_is_normalized_to_lowercase(self):
        self._post_update(self.user, self._valid_data(username="Carla.Campo"))

        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.username, "carla.campo")

    def test_username_with_spaces_is_invalid(self):
        response = self._post_update(
            self.user,
            self._valid_data(username="Claudia Campo"),
        )

        self.assertEqual(response.status_code, 200)
        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.username, "carla.comercial")
        self.assertIn("username", response.context["form"].errors)

    def test_duplicate_username_does_not_save(self):
        response = self._post_update(
            self.user,
            self._valid_data(username=self.other_user.username),
        )

        self.assertEqual(response.status_code, 200)
        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.username, "carla.comercial")

    def test_edit_name_and_email(self):
        self._post_update(
            self.user,
            self._valid_data(
                first_name="Carla María",
                last_name="Campo",
                email="carla.campo@example.com",
            ),
        )

        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.first_name, "Carla María")
        self.assertEqual(self.managed_user.last_name, "Campo")
        self.assertEqual(self.managed_user.email, "carla.campo@example.com")

    def test_change_role_from_commercial_to_management(self):
        self._post_update(self.user, self._valid_data(role=MANAGEMENT_GROUP))

        self.managed_user.refresh_from_db()
        self.assertEqual(
            list(self.managed_user.groups.values_list("name", flat=True)),
            [MANAGEMENT_GROUP],
        )

    def test_role_change_leaves_exactly_one_group(self):
        self.managed_user.groups.add(self.warehouse_group)
        self._post_update(self.user, self._valid_data(role=MANAGEMENT_GROUP))

        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.groups.count(), 1)
        self.assertEqual(
            self.managed_user.groups.get().name,
            MANAGEMENT_GROUP,
        )

    def test_legacy_role_is_not_available(self):
        response = self._post_update(
            self.user,
            self._valid_data(role=LEGACY_ADMIN_WAREHOUSE_GROUP),
        )

        self.assertEqual(response.status_code, 200)
        self.managed_user.refresh_from_db()
        self.assertEqual(
            list(self.managed_user.groups.values_list("name", flat=True)),
            [COMMERCIAL_GROUP],
        )
        self.assertIn("role", response.context["form"].errors)

    def test_duplicate_email_does_not_save(self):
        response = self._post_update(
            self.user,
            self._valid_data(email=self.other_user.email),
        )

        self.assertEqual(response.status_code, 200)
        self.managed_user.refresh_from_db()
        self.assertEqual(self.managed_user.email, "carla.comercial@example.com")

    def test_empty_email_is_normalized_to_none(self):
        self._post_update(self.user, self._valid_data(email=""))

        self.managed_user.refresh_from_db()
        self.assertIsNone(self.managed_user.email)

    def test_administrator_can_edit_another_account(self):
        response = self._post_update(
            self.user,
            self._valid_data(
                first_name="Carla Editada",
                role=MANAGEMENT_GROUP,
            ),
        )

        self.managed_user.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("accounts:user_detail", args=[self.managed_user.pk]),
        )
        self.assertEqual(self.managed_user.first_name, "Carla Editada")
        self.assertEqual(
            list(self.managed_user.groups.values_list("name", flat=True)),
            [MANAGEMENT_GROUP],
        )

    def test_administrator_cannot_remove_own_admin_role(self):
        response = self._post_update(
            self.user,
            self._valid_data(user=self.user, role=WAREHOUSE_GROUP),
            url=self.self_url,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No puedes quitarte tu propio rol de Administrador.",
        )
        self.user.refresh_from_db()
        self.assertEqual(
            list(self.user.groups.values_list("name", flat=True)),
            [ADMIN_GROUP],
        )

    def test_edit_button_requires_change_permission(self):
        detail_url = reverse(
            "accounts:user_detail",
            args=[self.managed_user.pk],
        )

        self.client.force_login(self.viewer)
        hidden = self.client.get(detail_url)
        self.assertNotContains(hidden, ">Editar</a>")
        self.assertNotContains(hidden, f'href="{self.url}"')

        self.client.force_login(self.user)
        visible = self.client.get(detail_url)
        self.assertContains(visible, "Editar")
        self.assertContains(visible, f'href="{self.url}"')


class UserToggleActiveViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="change_user",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )
        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)

        self.user = User.objects.create_user(
            username="admin.editor",
            email="admin.editor@example.com",
            password="pass",
        )
        self.user.user_permissions.add(change_permission, view_permission)
        self.user.groups.add(admin_group)
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
        self.managed_user = User.objects.create_user(
            username="carla.comercial",
            email="carla.comercial@example.com",
            password="pass",
        )
        self.url = reverse(
            "accounts:user_toggle_active",
            args=[self.managed_user.pk],
        )
        self.detail_url = reverse(
            "accounts:user_detail",
            args=[self.managed_user.pk],
        )
        self.self_url = reverse(
            "accounts:user_toggle_active",
            args=[self.user.pk],
        )
        self.self_detail_url = reverse(
            "accounts:user_detail",
            args=[self.user.pk],
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
        self.managed_user.refresh_from_db()
        self.assertTrue(self.managed_user.is_active)

    def test_get_does_not_change_active_state(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.managed_user.refresh_from_db()
        self.assertTrue(self.managed_user.is_active)

    def test_post_deactivates_active_user(self):
        self._post_toggle(self.user)

        self.managed_user.refresh_from_db()
        self.assertFalse(self.managed_user.is_active)

    def test_post_activates_inactive_user(self):
        self.managed_user.is_active = False
        self.managed_user.save(update_fields=["is_active"])

        self._post_toggle(self.user)

        self.managed_user.refresh_from_db()
        self.assertTrue(self.managed_user.is_active)

    def test_missing_user_returns_404(self):
        missing_url = reverse(
            "accounts:user_toggle_active",
            args=[self.managed_user.pk + 999],
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
            '<button type="submit" class="sgot-btn sgot-btn-danger">Desactivar usuario</button>',
            html=True,
        )
        self.assertContains(response, f'action="{self.url}"')
        self.assertNotContains(
            response,
            '<button type="submit" class="sgot-btn sgot-btn-secondary">Activar usuario</button>',
            html=True,
        )

    def test_user_without_change_permission_does_not_see_action(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url)

        self.assertNotContains(response, "Desactivar usuario")
        self.assertNotContains(response, "Activar usuario")
        self.assertNotContains(response, f'action="{self.url}"')

    def test_administrator_can_deactivate_another_account(self):
        self._post_toggle(self.user)

        self.managed_user.refresh_from_db()
        self.assertFalse(self.managed_user.is_active)

    def test_own_detail_does_not_show_deactivate_button(self):
        self.client.force_login(self.user)
        response = self.client.get(self.self_detail_url)

        self.assertNotContains(response, "Desactivar usuario")
        self.assertNotContains(response, f'action="{self.self_url}"')

    def test_administrator_cannot_deactivate_own_account(self):
        response = self._post_toggle(self.user, self.self_url)

        self.assertRedirects(
            response,
            self.self_detail_url,
            fetch_redirect_response=False,
        )
        self.assertContains(
            self.client.get(self.self_detail_url),
            "No puedes desactivar tu propia cuenta.",
        )

    def test_self_deactivation_attempt_keeps_account_active(self):
        self._post_toggle(self.user, self.self_url)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)


class UserResetPasswordViewTests(TestCase):
    def setUp(self):
        change_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="change_user",
        )
        view_permission = Permission.objects.get(
            content_type__app_label="accounts",
            codename="view_user",
        )
        admin_group, _ = Group.objects.get_or_create(name=ADMIN_GROUP)

        self.user = User.objects.create_user(
            username="admin.editor",
            email="admin.editor@example.com",
            password="SgotAnterior123",
        )
        self.user.user_permissions.add(change_permission, view_permission)
        self.user.groups.add(admin_group)
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
        self.managed_user = User.objects.create_user(
            username="carla.comercial",
            email="carla.comercial@example.com",
            password="SgotAnterior123",
        )
        self.url = reverse(
            "accounts:user_reset_password",
            args=[self.managed_user.pk],
        )
        self.detail_url = reverse(
            "accounts:user_detail",
            args=[self.managed_user.pk],
        )
        self.self_url = reverse(
            "accounts:user_reset_password",
            args=[self.user.pk],
        )
        self.self_detail_url = reverse(
            "accounts:user_detail",
            args=[self.user.pk],
        )

    def _valid_data(self, **overrides):
        data = {
            "new_password1": "SgotNuevaClave456",
            "new_password2": "SgotNuevaClave456",
        }
        data.update(overrides)
        return data

    def _post_reset(self, user, url=None, data=None):
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
        self.assertContains(response, "Su contraseña")
        self.assertNotContains(response, "Your password")

    def test_valid_post_changes_password(self):
        self._post_reset(self.user)

        self.managed_user.refresh_from_db()
        self.assertTrue(self.managed_user.check_password("SgotNuevaClave456"))

    def test_previous_password_stops_working(self):
        self._post_reset(self.user)

        self.managed_user.refresh_from_db()
        self.assertFalse(self.managed_user.check_password("SgotAnterior123"))

    def test_mismatched_passwords_do_not_change_password(self):
        response = self._post_reset(
            self.user,
            data=self._valid_data(new_password2="OtraClave123"),
        )

        self.assertEqual(response.status_code, 200)
        self.managed_user.refresh_from_db()
        self.assertTrue(self.managed_user.check_password("SgotAnterior123"))

    def test_weak_password_uses_django_validation_in_spanish(self):
        response = self._post_reset(
            self.user,
            data=self._valid_data(
                new_password1="123",
                new_password2="123",
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "demasiado corta")
        self.managed_user.refresh_from_db()
        self.assertTrue(self.managed_user.check_password("SgotAnterior123"))

    def test_valid_post_redirects_to_detail(self):
        response = self._post_reset(self.user)

        self.assertRedirects(response, self.detail_url)

    def test_reset_password_button_requires_change_permission(self):
        self.client.force_login(self.viewer)
        hidden = self.client.get(self.detail_url)
        self.assertNotContains(hidden, "Restablecer contraseña")
        self.assertNotContains(hidden, f'href="{self.url}"')

        self.client.force_login(self.user)
        visible = self.client.get(self.detail_url)
        self.assertContains(visible, "Restablecer contraseña")
        self.assertContains(visible, f'href="{self.url}"')

    def test_resetting_own_password_keeps_session(self):
        self.client.force_login(self.user)
        response = self.client.post(self.self_url, self._valid_data())

        self.assertRedirects(response, self.self_detail_url)
        follow = self.client.get(self.self_detail_url)
        self.assertEqual(follow.status_code, 200)
        self.assertEqual(follow.wsgi_request.user.pk, self.user.pk)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("SgotNuevaClave456"))

    def test_missing_user_returns_404(self):
        missing_url = reverse(
            "accounts:user_reset_password",
            args=[self.managed_user.pk + 999],
        )
        response = self._post_reset(self.user, url=missing_url)

        self.assertEqual(response.status_code, 404)


class LoginViewTests(TestCase):
    def setUp(self):
        self.url = reverse("accounts:login")
        self.user = User.objects.create_user(
            username="operador",
            email="operador@example.com",
            password="SgotClave123",
        )
        self.inactive_user = User.objects.create_user(
            username="usuario.bloqueado",
            email="bloqueado@example.com",
            password="SgotClave123",
            is_active=False,
        )

    def test_login_uses_expected_template(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(response, "SGOT")
        self.assertContains(response, "Iniciar sesión")

    def test_invalid_credentials_show_spanish_error(self):
        response = self.client.post(
            self.url,
            {"username": "operador", "password": "incorrecta"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Por favor")
        self.assertContains(response, "clave correctos")
        self.assertNotContains(response, "Please enter")

    def test_inactive_user_login_is_rejected_without_revealing_status(self):
        response = self.client.post(
            self.url,
            {"username": "usuario.bloqueado", "password": "SgotClave123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertContains(response, "clave correctos")
        content = response.content.decode()
        self.assertNotIn("inactiv", content.lower())
        self.assertNotIn("desactivad", content.lower())
