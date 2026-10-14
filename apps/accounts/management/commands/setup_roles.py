from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from apps.accounts.constants import (
    ADMIN_GROUP,
    COMMERCIAL_GROUP,
    DEFAULT_GROUPS,
    MANAGEMENT_GROUP,
    TECHNICAL_MANAGER_GROUP,
    WAREHOUSE_GROUP,
)


def _get_permission(app_label, codename):
    return Permission.objects.get(
        content_type__app_label=app_label,
        codename=codename,
    )


OPERATIONAL_PERMISSIONS = [
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
]

ADMIN_USER_PERMISSIONS = [
    ("accounts", "view_user"),
    ("accounts", "add_user"),
    ("accounts", "change_user"),
]

GROUP_PERMISSIONS = {
    ADMIN_GROUP: [
        *OPERATIONAL_PERMISSIONS,
        *ADMIN_USER_PERMISSIONS,
    ],
    WAREHOUSE_GROUP: list(OPERATIONAL_PERMISSIONS),
    COMMERCIAL_GROUP: [
        ("customers", "view_customer"),
        ("catalog", "view_product"),
        ("catalog", "view_worktype"),
        ("workorders", "view_workorder"),
        ("workorders", "view_workorderitem"),
    ],
    TECHNICAL_MANAGER_GROUP: [
        ("customers", "view_customer"),
        ("catalog", "view_product"),
        ("catalog", "view_technician"),
        ("catalog", "view_worktype"),
        ("workorders", "view_workorder"),
        ("workorders", "view_workorderitem"),
        ("workorders", "schedule_workorder"),
    ],
    MANAGEMENT_GROUP: [
        ("customers", "view_customer"),
        ("catalog", "view_product"),
        ("catalog", "view_technician"),
        ("catalog", "view_worktype"),
        ("workorders", "view_workorder"),
        ("workorders", "view_workorderitem"),
        ("workorders", "view_workorderhistory"),
        ("warehouse", "view_warehouseoutput"),
        ("warehouse", "view_warehouseoutputitem"),
    ],
}


class Command(BaseCommand):
    help = "Crea los grupos de roles iniciales del sistema SGOT y asigna sus permisos."

    def handle(self, *args, **options):
        for group_name in DEFAULT_GROUPS:
            group, created = Group.objects.get_or_create(name=group_name)

            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group.name}" creado.'))
            else:
                self.stdout.write(f'Grupo "{group.name}" ya existía.')

            permissions = [
                _get_permission(app_label, codename)
                for app_label, codename in GROUP_PERMISSIONS[group_name]
            ]
            group.permissions.set(permissions)
            self.stdout.write(f'Permisos asignados a "{group.name}".')

        self.stdout.write(self.style.SUCCESS("Roles iniciales configurados correctamente."))
