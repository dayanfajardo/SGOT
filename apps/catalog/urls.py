from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/edit/", views.product_update, name="product_update"),
    path(
        "products/<int:pk>/toggle-active/",
        views.product_toggle_active,
        name="product_toggle_active",
    ),
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
