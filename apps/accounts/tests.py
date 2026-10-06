from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase

from apps.accounts.constants import TECHNICAL_MANAGER_GROUP


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
