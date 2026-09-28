from django.urls import path

from apps.warehouse import views

app_name = "warehouse"

urlpatterns = [
    path(
        "workorders/<int:work_order_pk>/warehouse-output/new/",
        views.warehouse_output_create,
        name="warehouse_output_create",
    ),
]
