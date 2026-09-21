from django.contrib import admin

from .models import Product, Technician, WorkType


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "reference",
        "product_type",
        "unit",
        "active",
    )
    search_fields = (
        "name",
        "reference",
    )
    list_filter = (
        "product_type",
        "unit",
        "active",
    )


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "technician_type",
        "phone",
        "active",
    )
    search_fields = (
        "first_name",
        "last_name",
        "phone",
    )
    list_filter = (
        "technician_type",
        "active",
    )


@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "active",
    )
    search_fields = (
        "name",
        "description",
    )
    list_filter = ("active",)
