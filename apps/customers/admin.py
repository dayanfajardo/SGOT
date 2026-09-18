from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "trade_name",
        "customer_code",
        "code_system",
        "document",
        "phone",
    )
    search_fields = (
        "trade_name",
        "customer_code",
        "legal_name",
        "document",
    )
    list_filter = ("code_system",)
