from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.constants import (
    ADMIN_WAREHOUSE_GROUP,
    COMMERCIAL_GROUP,
    MANAGEMENT_GROUP,
    TECHNICAL_MANAGER_GROUP,
)
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

        self.commercial_group, _ = Group.objects.get_or_create(name=COMMERCIAL_GROUP)
        self.admin_group, _ = Group.objects.get_or_create(
            name=ADMIN_WAREHOUSE_GROUP
        )
        self.technical_group, _ = Group.objects.get_or_create(
            name=TECHNICAL_MANAGER_GROUP
        )
        self.management_group, _ = Group.objects.get_or_create(
            name=MANAGEMENT_GROUP
        )

        for group in (
            self.commercial_group,
            self.admin_group,
            self.technical_group,
            self.management_group,
        ):
            group.permissions.add(view_permission)

        self.customer = Customer.objects.create(
            trade_name="Cliente Lista",
            customer_code="CLI-100",
            code_system=Customer.CodeSystem.CENTURION,
        )
        self.other_customer = Customer.objects.create(
            trade_name="Acme Seguridad",
            customer_code="ACM-01",
            code_system=Customer.CodeSystem.ARION,
        )
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )
        self.other_technician = Technician.objects.create(
            first_name="Luis",
            last_name="Rojas",
            technician_type=Technician.TechnicianType.CONTRACTOR,
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
            scheduled_date=date(2026, 9, 20),
        )
        self.other_order = self._create_work_order(
            number="OT-1002",
            commercial=self.other_commercial,
            customer=self.other_customer,
            technician=self.other_technician,
            status=WorkOrder.Status.IN_INSTALLATION,
            received_date=date(2026, 9, 11),
            scheduled_date=date(2026, 9, 25),
        )

    def _create_user(self, username, group):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="pass",
        )
        user.groups.add(group)
        return user

    def _create_work_order(
        self,
        *,
        number,
        commercial,
        customer=None,
        technician=None,
        status=WorkOrder.Status.RECEIVED,
        received_date=None,
        scheduled_date=None,
    ):
        return WorkOrder.objects.create(
            number=number,
            customer=customer or self.customer,
            commercial=commercial,
            work_type=self.work_type,
            assigned_technician=technician or self.technician,
            status=status,
            received_date=received_date or date(2026, 9, 10),
            scheduled_date=scheduled_date,
            created_by=commercial,
        )

    def _get_list(self, user, params=None):
        self.client.force_login(user)
        return self.client.get(self.url, data=params or {})

    def _orders(self, response):
        return list(response.context["work_orders"])

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
        self.assertEqual(self._orders(response), [self.own_order])

    def test_commercial_does_not_see_other_commercial_orders(self):
        response = self._get_list(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.other_order.number)
        self.assertNotIn(self.other_order, self._orders(response))

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

    def test_search_by_work_order_number(self):
        response = self._get_list(self.admin_user, {"q": "OT-1001"})

        self.assertEqual(self._orders(response), [self.own_order])

    def test_search_is_partial_and_case_insensitive(self):
        response = self._get_list(self.admin_user, {"q": "ot-1001"})

        self.assertEqual(self._orders(response), [self.own_order])

        response = self._get_list(self.admin_user, {"q": "1001"})

        self.assertEqual(self._orders(response), [self.own_order])
        self.assertNotIn(self.other_order, self._orders(response))

    def test_search_by_customer_trade_name(self):
        response = self._get_list(self.admin_user, {"q": "acme seguridad"})

        self.assertEqual(self._orders(response), [self.other_order])

    def test_search_by_customer_code(self):
        response = self._get_list(self.admin_user, {"q": "cli-100"})

        self.assertEqual(self._orders(response), [self.own_order])

    def test_filter_by_status(self):
        response = self._get_list(
            self.admin_user,
            {"status": WorkOrder.Status.IN_INSTALLATION},
        )

        self.assertEqual(self._orders(response), [self.other_order])

    def test_filter_by_assigned_technician(self):
        response = self._get_list(
            self.admin_user,
            {"technician": self.other_technician.pk},
        )

        self.assertEqual(self._orders(response), [self.other_order])

    def test_filter_by_commercial(self):
        response = self._get_list(
            self.admin_user,
            {"commercial": self.other_commercial.pk},
        )

        self.assertEqual(self._orders(response), [self.other_order])

    def test_filter_by_scheduled_date(self):
        response = self._get_list(
            self.admin_user,
            {"scheduled_date": "2026-09-20"},
        )

        self.assertEqual(self._orders(response), [self.own_order])

    def test_combined_search_and_status_filter(self):
        response = self._get_list(
            self.admin_user,
            {"q": "OT-100", "status": WorkOrder.Status.RECEIVED},
        )

        self.assertEqual(self._orders(response), [self.own_order])

    def test_combined_multiple_filters(self):
        response = self._get_list(
            self.admin_user,
            {
                "q": "OT-100",
                "status": WorkOrder.Status.IN_INSTALLATION,
                "technician": self.other_technician.pk,
                "commercial": self.other_commercial.pk,
                "scheduled_date": "2026-09-25",
            },
        )

        self.assertEqual(self._orders(response), [self.other_order])

    def test_filters_without_matches_return_empty_queryset(self):
        response = self._get_list(self.admin_user, {"q": "ZZZ-NO-MATCH"})

        self.assertEqual(self._orders(response), [])

    def test_filter_form_is_in_context(self):
        response = self._get_list(self.admin_user)

        self.assertIn("filter_form", response.context)
        self.assertIsInstance(response.context["filter_form"], WorkOrderFilterForm)

    def test_commercial_filter_form_does_not_include_commercial_field(self):
        response = self._get_list(self.commercial)

        self.assertNotIn("commercial", response.context["filter_form"].fields)

    def test_commercial_scope_ignores_manual_query_params(self):
        response = self._get_list(
            self.commercial,
            {
                "commercial": self.other_commercial.pk,
                "q": self.other_order.number,
                "status": WorkOrder.Status.IN_INSTALLATION,
            },
        )

        self.assertNotIn(self.other_order, self._orders(response))

        response = self._get_list(
            self.commercial,
            {"commercial": self.other_commercial.pk},
        )

        self.assertEqual(self._orders(response), [self.own_order])
        self.assertNotIn(self.other_order, self._orders(response))

    def test_non_commercial_authorized_user_can_filter_by_commercial(self):
        response = self._get_list(
            self.admin_user,
            {"commercial": self.other_commercial.pk},
        )

        self.assertEqual(self._orders(response), [self.other_order])
        self.assertIn("commercial", response.context["filter_form"].fields)

        response = self._get_list(
            self.technical_user,
            {"commercial": self.commercial.pk},
        )

        self.assertEqual(self._orders(response), [self.own_order])

    def test_empty_filters_keep_unfiltered_list(self):
        unfiltered = self._get_list(self.admin_user)
        empty_filters = self._get_list(
            self.admin_user,
            {
                "q": "",
                "status": "",
                "technician": "",
                "commercial": "",
                "scheduled_date": "",
            },
        )

        self.assertEqual(
            self._orders(empty_filters),
            self._orders(unfiltered),
        )
        self.assertEqual(
            self._orders(empty_filters),
            [self.other_order, self.own_order],
        )
