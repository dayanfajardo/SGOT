from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from apps.workorders.models import WorkOrder


@login_required
def work_order_list(request):
    if not request.user.has_perm("workorders.view_workorder"):
        raise PermissionDenied

    work_orders = WorkOrder.objects.select_related(
        "customer",
        "commercial",
        "work_type",
        "assigned_technician",
    )

    if request.user.groups.filter(name="Comercial").exists():
        work_orders = work_orders.filter(commercial=request.user)

    return render(
        request,
        "workorders/workorder_list.html",
        {"work_orders": work_orders},
    )
