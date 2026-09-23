from django.urls import path

from apps.workorders import views

app_name = "workorders"

urlpatterns = [
    path("workorders/", views.work_order_list, name="workorder_list"),
]
