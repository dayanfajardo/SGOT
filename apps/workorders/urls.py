from django.urls import path

from apps.workorders import views

app_name = "workorders"

urlpatterns = [
    path("workorders/", views.work_order_list, name="workorder_list"),
    path(
        "workorders/new/",
        views.work_order_create,
        name="workorder_create",
    ),
    path(
        "workorders/<int:pk>/",
        views.work_order_detail,
        name="workorder_detail",
    ),
    path(
        "workorders/<int:pk>/schedule/",
        views.work_order_schedule,
        name="workorder_schedule",
    ),
    path(
        "workorders/<int:pk>/status/",
        views.work_order_change_status,
        name="workorder_change_status",
    ),
    path(
        "workorders/<int:pk>/start-installation/",
        views.work_order_start_installation,
        name="workorder_start_installation",
    ),
]
