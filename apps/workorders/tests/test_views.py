from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import COMMERCIAL_GROUP
from apps.catalog.models import Technician, WorkType
from apps.customers.models import Customer
from apps.workorders.forms import WorkOrderFilterForm
from apps.workorders.models import WorkOrder

User = get_user_model()


class WorkOrderListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("workorders:workorder_list")

        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )

        self.commercial_group, _ = Group.objects.get_or_create(name="Comercial")
        self.admin_group, _ = Group.objects.get_or_create(
            name="Administrador / Almacén"
        )
        self.technical_group, _ = Group.objects.get_or_create(name="Jefe Técnica")
        self.management_group, _ = Group.objects.get_or_create(name="Gerencia")

        for group in (
            self.commercial_group,
            self.admin_group,
            self.technical_group,
            self.management_group,
        ):
            group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Lista")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )

        self.commercial = self._create_user("comercial.uno", self.commercial_group)
        self.other_commercial = self._create_user(
            "comercial.dos",
            self.commercial_group,
        )
        self.admin_user = self._create_user("admin.almacen", self.admin_group)
        self.technical_user = self._create_user(
            "jefe.tecnica",
            self.technical_group,
        )
        self.management_user = self._create_user(
            "gerencia",
            self.management_group,
        )
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.own_order = self._create_work_order(
            number="OT-1001",
            commercial=self.commercial,
        )
        self.other_order = self._create_work_order(
            number="OT-1002",
            commercial=self.other_commercial,
        )

    def _create_user(self, username, group):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )
        user.groups.add(group)
        return user

    def _create_work_order(self, *, number, commercial):
        return WorkOrder.objects.create(
            number=number,
            customer=self.customer,
            commercial=commercial,
            work_type=self.work_type,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 10),
            created_by=commercial,
        )

    def _get_list(self, user):
        self.client.force_login(user)
        return self.client.get(self.url)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_list(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_commercial_sees_only_own_orders(self):
        response = self._get_list(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertEqual(list(response.context["work_orders"]), [self.own_order])

    def test_commercial_does_not_see_other_commercial_orders(self):
        response = self._get_list(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.other_order.number)
        self.assertNotIn(self.other_order, response.context["work_orders"])

    def test_admin_warehouse_sees_all_orders(self):
        response = self._get_list(self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.other_order.number)

    def test_technical_manager_sees_all_orders(self):
        response = self._get_list(self.technical_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.other_order.number)

    def test_management_sees_all_orders(self):
        response = self._get_list(self.management_user)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.own_order.number)
        self.assertContains(response, self.other_order.number)

    def test_list_uses_workorder_list_template(self):
        response = self._get_list(self.admin_user)

        self.assertTemplateUsed(response, "workorders/workorder_list.html")

    def test_list_includes_filter_form(self):
        response = self._get_list(self.admin_user)

        self.assertIn("filter_form", response.context)
        self.assertIsInstance(response.context["filter_form"], WorkOrderFilterForm)
        self.assertContains(response, "Buscar OT o cliente...")
        self.assertContains(response, 'name="commercial"')

    def test_commercial_does_not_see_commercial_filter(self):
        response = self._get_list(self.commercial)

        self.assertNotIn("commercial", response.context["filter_form"].fields)
        self.assertNotContains(response, 'id="id_commercial"')
        self.assertContains(response, "Buscar OT o cliente...")
        self.assertContains(response, "Comercial")


class WorkOrderListFilterTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("workorders:workorder_list")

        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )
        self.commercial_group, _ = Group.objects.get_or_create(name=COMMERCIAL_GROUP)
        self.admin_group, _ = Group.objects.get_or_create(
            name="Administrador / Almacén"
        )
        self.commercial_group.permissions.add(view_permission)
        self.admin_group.permissions.add(view_permission)

        self.admin_user = User.objects.create_user(
            username="admin.filtros",
            email="admin.filtros@example.com",
            password="pass",
        )
        self.admin_user.groups.add(self.admin_group)

        self.commercial = User.objects.create_user(
            username="comercial.alpha",
            email="comercial.alpha@example.com",
            password="pass",
        )
        self.commercial.groups.add(self.commercial_group)
        self.other_commercial = User.objects.create_user(
            username="comercial.beta",
            email="comercial.beta@example.com",
            password="pass",
        )
        self.other_commercial.groups.add(self.commercial_group)

        self.work_type = WorkType.objects.create(name="Instalación alarmas")
        self.technician = Technician.objects.create(
            first_name="Ana",
            last_name="Gómez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.other_technician = Technician.objects.create(
            first_name="Luis",
            last_name="Rojas",
            technician_type=Technician.TechnicianType.CONTRACTOR,
        )
        self.inactive_technician = Technician.objects.create(
            first_name="Marta",
            last_name="Inactiva",
            technician_type=Technician.TechnicianType.STAFF,
            active=False,
        )

        self.acme = Customer.objects.create(
            trade_name="Acme Seguridad",
            customer_code="ACM-01",
            code_system=Customer.CodeSystem.CENTURION,
        )
        self.beta = Customer.objects.create(
            trade_name="Beta Alarmas",
            customer_code="BET-22",
            code_system=Customer.CodeSystem.ARION,
        )

        self.order_acme = WorkOrder.objects.create(
            number="OT-2001",
            customer=self.acme,
            commercial=self.commercial,
            work_type=self.work_type,
            status=WorkOrder.Status.RECEIVED,
            assigned_technician=self.technician,
            received_date=date(2026, 9, 10),
            scheduled_date=date(2026, 9, 20),
            created_by=self.admin_user,
        )
        self.order_beta = WorkOrder.objects.create(
            number="OT-2002",
            customer=self.beta,
            commercial=self.other_commercial,
            work_type=self.work_type,
            status=WorkOrder.Status.IN_INSTALLATION,
            assigned_technician=self.other_technician,
            received_date=date(2026, 9, 11),
            scheduled_date=date(2026, 9, 25),
            created_by=self.admin_user,
        )

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _numbers(self, response):
        return [order.number for order in response.context["work_orders"]]

    def test_search_by_work_order_number(self):
        response = self._get_list(self.admin_user, {"q": "ot-2001"})

        self.assertEqual(self._numbers(response), ["OT-2001"])

    def test_search_by_customer_trade_name(self):
        response = self._get_list(self.admin_user, {"q": "beta alarm"})

        self.assertEqual(self._numbers(response), ["OT-2002"])

    def test_search_by_customer_code(self):
        response = self._get_list(self.admin_user, {"q": "acm-01"})

        self.assertEqual(self._numbers(response), ["OT-2001"])

    def test_filter_by_status(self):
        response = self._get_list(
            self.admin_user,
            {"status": WorkOrder.Status.IN_INSTALLATION},
        )

        self.assertEqual(self._numbers(response), ["OT-2002"])

    def test_filter_by_technician(self):
        response = self._get_list(
            self.admin_user,
            {"technician": self.technician.pk},
        )

        self.assertEqual(self._numbers(response), ["OT-2001"])

    def test_filter_by_commercial(self):
        response = self._get_list(
            self.admin_user,
            {"commercial": self.other_commercial.pk},
        )

        self.assertEqual(self._numbers(response), ["OT-2002"])

    def test_filter_by_scheduled_date(self):
        response = self._get_list(
            self.admin_user,
            {"scheduled_date": "2026-09-20"},
        )

        self.assertEqual(self._numbers(response), ["OT-2001"])

    def test_combined_search_and_status_filter(self):
        response = self._get_list(
            self.admin_user,
            {"q": "OT-200", "status": WorkOrder.Status.RECEIVED},
        )

        self.assertEqual(self._numbers(response), ["OT-2001"])

    def test_commercial_scope_applies_before_filters(self):
        response = self._get_list(
            self.commercial,
            {"q": "OT-200", "commercial": self.other_commercial.pk},
        )

        self.assertEqual(self._numbers(response), ["OT-2001"])
        self.assertNotIn(self.order_beta, response.context["work_orders"])

    def test_no_results_with_active_filters_shows_clear_message(self):
        response = self._get_list(self.admin_user, {"q": "no-existe"})

        self.assertEqual(self._numbers(response), [])
        self.assertTrue(response.context["has_work_orders"])
        self.assertContains(
            response,
            "No encontramos órdenes con los filtros seleccionados.",
        )
        self.assertContains(response, "Limpiar filtros")
        self.assertNotContains(response, "No hay órdenes de trabajo para mostrar.")

    def test_empty_catalog_message_when_user_has_no_orders(self):
        empty_commercial = User.objects.create_user(
            username="comercial.vacio",
            email="comercial.vacio@example.com",
            password="pass",
        )
        empty_commercial.groups.add(self.commercial_group)

        response = self._get_list(empty_commercial)

        self.assertFalse(response.context["has_work_orders"])
        self.assertContains(response, "No hay órdenes de trabajo para mostrar.")
        self.assertNotContains(
            response,
            "No encontramos órdenes con los filtros seleccionados.",
        )

    def test_filter_form_excludes_inactive_technicians(self):
        form = WorkOrderFilterForm()

        self.assertQuerySetEqual(
            form.fields["technician"].queryset,
            [self.technician, self.other_technician],
            transform=lambda technician: technician,
        )
        self.assertNotIn(self.inactive_technician, form.fields["technician"].queryset)

    def test_filter_form_commercials_are_ordered_by_username(self):
        form = WorkOrderFilterForm()

        self.assertEqual(
            list(form.fields["commercial"].queryset),
            [self.commercial, self.other_commercial],
        )

    def test_clear_link_points_to_list_without_query_params(self):
        response = self._get_list(self.admin_user, {"q": "OT-2001"})

        self.assertContains(response, f'href="{self.url}"')
        self.assertNotContains(response, f'href="{self.url}?')
