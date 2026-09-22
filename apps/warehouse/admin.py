from django.contrib import admin

from .models import WarehouseOutput, WarehouseOutputItem


class WarehouseOutputItemInline(admin.TabularInline):
    model = WarehouseOutputItem
    extra = 1
    fields = (
        "product",
        "work_order_item",
        "delivered_quantity",
        "returned_quantity",
        "notes",
    )


@admin.register(WarehouseOutput)
class WarehouseOutputAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "work_order",
        "technician",
        "output_date",
        "created_by",
    )
    search_fields = (
        "number",
        "work_order__number",
        "work_order__customer__trade_name",
        "technician__first_name",
        "technician__last_name",
    )
    list_filter = (
        "output_date",
        "technician",
    )
    date_hierarchy = "output_date"
    inlines = (WarehouseOutputItemInline,)
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Información de la salida",
            {
                "fields": (
                    "number",
                    "work_order",
                    "technician",
                    "output_date",
                ),
            },
        ),
        (
            "Información adicional",
            {
                "fields": (
                    "notes",
                    "created_by",
                ),
            },
        ),
    )
