from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("technicians/", views.technician_list, name="technician_list"),
    path("technicians/new/", views.technician_create, name="technician_create"),
    path(
        "technicians/<int:pk>/",
        views.technician_detail,
        name="technician_detail",
    ),
    path(
        "technicians/<int:pk>/edit/",
        views.technician_update,
        name="technician_update",
    ),
    path(
        "technicians/<int:pk>/toggle-active/",
        views.technician_toggle_active,
        name="technician_toggle_active",
    ),
]
