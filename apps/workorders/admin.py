from django.contrib import admin

from .models import WorkOrder, WorkOrderHistory, WorkOrderItem


class WorkOrderItemInline(admin.TabularInline):
    model = WorkOrderItem
    extra = 1
    fields = (
        "product",
        "requested_quantity",
        "notes",
    )


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "customer",
        "work_type",
        "status",
        "assigned_technician",
        "received_date",
        "scheduled_date",
    )
    search_fields = (
        "number",
        "customer__trade_name",
        "customer__customer_code",
    )
    list_filter = (
        "status",
        "work_type",
        "assigned_technician",
        "received_date",
    )
    date_hierarchy = "received_date"
    inlines = (WorkOrderItemInline,)
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (
            "Información de la orden",
            {
                "fields": (
                    "number",
                    "customer",
                    "commercial",
                    "work_type",
                    "received_date",
                ),
            },
        ),
        (
            "Estado y programación",
            {
                "fields": (
                    "status",
                    "assigned_technician",
                    "scheduled_date",
                    "installation_started_at",
                    "completed_at",
                ),
            },
        ),
        (
            "Información adicional",
            {
                "fields": (
                    "installation_address",
                    "notes",
                    "created_by",
                ),
            },
        ),
    )


@admin.register(WorkOrderHistory)
class WorkOrderHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "work_order",
        "event_type",
        "user",
        "created_at",
    )
    search_fields = (
        "work_order__number",
        "description",
    )
    list_filter = (
        "event_type",
        "created_at",
    )
    readonly_fields = (
        "work_order",
        "user",
        "event_type",
        "description",
        "previous_value",
        "new_value",
        "created_at",
    )
