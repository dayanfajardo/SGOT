from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.constants import ADMIN_WAREHOUSE_GROUP, COMMERCIAL_GROUP
from apps.catalog.models import Technician, WorkType
from apps.customers.models import Customer
from apps.workorders.models import WorkOrder

User = get_user_model()


class DashboardViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("workorders:dashboard")
        self.today = timezone.localdate()

        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )
        self.admin_group, _ = Group.objects.get_or_create(
            name=ADMIN_WAREHOUSE_GROUP
        )
        self.commercial_group, _ = Group.objects.get_or_create(
            name=COMMERCIAL_GROUP
        )
        self.admin_group.permissions.add(view_permission)
        self.commercial_group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Dashboard")
        self.work_type = WorkType.objects.create(name="Instalación CCTV")
        self.technician = Technician.objects.create(
            first_name="Carlos",
            last_name="Pérez",
            technician_type=Technician.TechnicianType.STAFF,
        )

        self.admin_user = self._create_user("admin.almacen", self.admin_group)
        self.commercial = self._create_user("comercial.uno", self.commercial_group)
        self.other_commercial = self._create_user(
            "comercial.dos",
            self.commercial_group,
        )
        self.user_without_permission = User.objects.create_user(
            username="sin.permiso",
            email="sin.permiso@example.com",
            password="pass",
        )

        self.own_received = self._create_work_order(
            number="OT-D-REC",
            commercial=self.commercial,
            status=WorkOrder.Status.RECEIVED,
        )
        self.own_pending = self._create_work_order(
            number="OT-D-PE",
            commercial=self.commercial,
            status=WorkOrder.Status.PENDING_EQUIPMENT,
        )
        self.own_today = self._create_work_order(
            number="OT-D-OK",
            commercial=self.commercial,
            status=WorkOrder.Status.EQUIPMENT_OK,
            scheduled_date=self.today,
        )
        self.own_overdue = self._create_work_order(
            number="OT-D-INS",
            commercial=self.commercial,
            status=WorkOrder.Status.IN_INSTALLATION,
            scheduled_date=self.today - timedelta(days=2),
        )
        self.own_completed_past = self._create_work_order(
            number="OT-D-COM",
            commercial=self.commercial,
            status=WorkOrder.Status.COMPLETED,
            scheduled_date=self.today - timedelta(days=10),
        )
        self.own_upcoming = self._create_work_order(
            number="OT-D-UP",
            commercial=self.commercial,
            status=WorkOrder.Status.EQUIPMENT_OK,
            scheduled_date=self.today + timedelta(days=3),
        )
        self.own_completed_today = self._create_work_order(
            number="OT-D-COM-TOD",
            commercial=self.commercial,
            status=WorkOrder.Status.COMPLETED,
            scheduled_date=self.today,
        )

        self.other_received = self._create_work_order(
            number="OT-D-OTH-REC",
            commercial=self.other_commercial,
            status=WorkOrder.Status.RECEIVED,
        )
        self.other_today = self._create_work_order(
            number="OT-D-OTH-TOD",
            commercial=self.other_commercial,
            status=WorkOrder.Status.PENDING_EQUIPMENT,
            scheduled_date=self.today,
        )
        self.other_overdue = self._create_work_order(
            number="OT-D-OTH-OV",
            commercial=self.other_commercial,
            status=WorkOrder.Status.IN_INSTALLATION,
            scheduled_date=self.today - timedelta(days=1),
        )
        self.other_upcoming = self._create_work_order(
            number="OT-D-OTH-UP",
            commercial=self.other_commercial,
            status=WorkOrder.Status.EQUIPMENT_OK,
            scheduled_date=self.today + timedelta(days=5),
        )
        self.other_completed_past = self._create_work_order(
            number="OT-D-OTH-COM",
            commercial=self.other_commercial,
            status=WorkOrder.Status.COMPLETED,
            scheduled_date=self.today - timedelta(days=5),
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
        status=WorkOrder.Status.RECEIVED,
        scheduled_date=None,
    ):
        return WorkOrder.objects.create(
            number=number,
            customer=self.customer,
            commercial=commercial,
            work_type=self.work_type,
            assigned_technician=self.technician,
            status=status,
            received_date=self.today - timedelta(days=15),
            scheduled_date=scheduled_date,
            created_by=commercial,
        )

    def _get_dashboard(self, user):
        self.client.force_login(user)
        return self.client.get(self.url)

    def _numbers(self, orders):
        return [order.number for order in orders]

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, f"/login/?next={self.url}")

    def test_authenticated_user_without_permission_gets_403(self):
        response = self._get_dashboard(self.user_without_permission)

        self.assertEqual(response.status_code, 403)

    def test_authorized_user_gets_200(self):
        response = self._get_dashboard(self.admin_user)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "workorders/dashboard.html")
        self.assertEqual(response.context["today"], self.today)

    def test_status_counts_for_authorized_user(self):
        response = self._get_dashboard(self.admin_user)

        self.assertEqual(response.context["received_count"], 2)
        self.assertEqual(response.context["pending_equipment_count"], 2)
        self.assertEqual(response.context["equipment_ok_count"], 3)
        self.assertEqual(response.context["in_installation_count"], 2)
        self.assertEqual(response.context["completed_count"], 3)

    def test_scheduled_today_count_excludes_completed(self):
        response = self._get_dashboard(self.admin_user)

        self.assertEqual(response.context["scheduled_today_count"], 2)

    def test_overdue_count(self):
        response = self._get_dashboard(self.admin_user)

        self.assertEqual(response.context["overdue_count"], 2)
        self.assertEqual(
            set(self._numbers(response.context["overdue_orders"])),
            {self.own_overdue.number, self.other_overdue.number},
        )

    def test_upcoming_count(self):
        response = self._get_dashboard(self.admin_user)

        self.assertEqual(response.context["upcoming_count"], 2)
        self.assertEqual(
            set(self._numbers(response.context["upcoming_orders"])),
            {self.own_upcoming.number, self.other_upcoming.number},
        )

    def test_completed_orders_are_not_counted_as_overdue(self):
        response = self._get_dashboard(self.admin_user)

        overdue_numbers = self._numbers(response.context["overdue_orders"])
        self.assertNotIn(self.own_completed_past.number, overdue_numbers)
        self.assertNotIn(self.other_completed_past.number, overdue_numbers)
        self.assertEqual(response.context["overdue_count"], 2)

    def test_commercial_counts_only_own_orders(self):
        response = self._get_dashboard(self.commercial)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["received_count"], 1)
        self.assertEqual(response.context["pending_equipment_count"], 1)
        self.assertEqual(response.context["equipment_ok_count"], 2)
        self.assertEqual(response.context["in_installation_count"], 1)
        self.assertEqual(response.context["completed_count"], 2)
        self.assertEqual(response.context["scheduled_today_count"], 1)
        self.assertEqual(response.context["overdue_count"], 1)
        self.assertEqual(response.context["upcoming_count"], 1)

    def test_commercial_overdue_orders_exclude_other_commercial(self):
        response = self._get_dashboard(self.commercial)

        overdue_orders = list(response.context["overdue_orders"])
        self.assertEqual(self._numbers(overdue_orders), [self.own_overdue.number])
        self.assertNotIn(self.other_overdue, overdue_orders)

    def test_commercial_upcoming_orders_exclude_other_commercial(self):
        response = self._get_dashboard(self.commercial)

        upcoming_orders = list(response.context["upcoming_orders"])
        self.assertEqual(self._numbers(upcoming_orders), [self.own_upcoming.number])
        self.assertNotIn(self.other_upcoming, upcoming_orders)


class DashboardOrderListTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("workorders:dashboard")
        self.today = timezone.localdate()

        view_permission = Permission.objects.get(
            content_type__app_label="workorders",
            codename="view_workorder",
        )
        self.admin_group, _ = Group.objects.get_or_create(
            name=ADMIN_WAREHOUSE_GROUP
        )
        self.admin_group.permissions.add(view_permission)

        self.customer = Customer.objects.create(trade_name="Cliente Listas")
        self.work_type = WorkType.objects.create(name="Mantenimiento")
        self.admin_user = User.objects.create_user(
            username="admin.listas",
            email="admin.listas@example.com",
            password="pass",
        )
        self.admin_user.groups.add(self.admin_group)

        overdue_specs = [
            (self.today - timedelta(days=9), "OT-OV-01"),
            (self.today - timedelta(days=8), "OT-OV-02"),
            (self.today - timedelta(days=7), "OT-OV-03"),
            (self.today - timedelta(days=6), "OT-OV-04"),
            (self.today - timedelta(days=5), "OT-OV-06"),
            (self.today - timedelta(days=5), "OT-OV-05"),
            (self.today - timedelta(days=4), "OT-OV-07"),
            (self.today - timedelta(days=3), "OT-OV-08"),
            (self.today - timedelta(days=2), "OT-OV-09"),
        ]
        upcoming_specs = [
            (self.today + timedelta(days=1), "OT-UP-01"),
            (self.today + timedelta(days=2), "OT-UP-02"),
            (self.today + timedelta(days=3), "OT-UP-03"),
            (self.today + timedelta(days=4), "OT-UP-04"),
            (self.today + timedelta(days=5), "OT-UP-06"),
            (self.today + timedelta(days=5), "OT-UP-05"),
            (self.today + timedelta(days=6), "OT-UP-07"),
            (self.today + timedelta(days=7), "OT-UP-08"),
            (self.today + timedelta(days=8), "OT-UP-09"),
        ]
        for scheduled_date, number in overdue_specs + upcoming_specs:
            WorkOrder.objects.create(
                number=number,
                customer=self.customer,
                commercial=self.admin_user,
                work_type=self.work_type,
                status=WorkOrder.Status.EQUIPMENT_OK,
                received_date=self.today - timedelta(days=20),
                scheduled_date=scheduled_date,
                created_by=self.admin_user,
            )

    def test_overdue_and_upcoming_lists_are_limited_and_ordered(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(self.url)

        overdue_numbers = [
            order.number for order in response.context["overdue_orders"]
        ]
        upcoming_numbers = [
            order.number for order in response.context["upcoming_orders"]
        ]

        self.assertEqual(len(overdue_numbers), 8)
        self.assertEqual(
            overdue_numbers,
            [
                "OT-OV-01",
                "OT-OV-02",
                "OT-OV-03",
                "OT-OV-04",
                "OT-OV-05",
                "OT-OV-06",
                "OT-OV-07",
                "OT-OV-08",
            ],
        )
        self.assertNotIn("OT-OV-09", overdue_numbers)

        self.assertEqual(len(upcoming_numbers), 8)
        self.assertEqual(
            upcoming_numbers,
            [
                "OT-UP-01",
                "OT-UP-02",
                "OT-UP-03",
                "OT-UP-04",
                "OT-UP-05",
                "OT-UP-06",
                "OT-UP-07",
                "OT-UP-08",
            ],
        )
        self.assertNotIn("OT-UP-09", upcoming_numbers)
        self.assertEqual(response.context["overdue_count"], 9)
        self.assertEqual(response.context["upcoming_count"], 9)
