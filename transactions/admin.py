from django.contrib import admin

from .models import FuelTransaction


@admin.register(FuelTransaction)
class FuelTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "external_reference",
        "card",
        "station",
        "fuel_type",
        "litres",
        "total_amount",
        "transaction_at",
    )
    search_fields = (
        "external_reference",
        "card__card_number",
        "card__company__name",
        "station__name",
    )
    list_filter = (
        "fuel_type",
        "station",
    )
    list_select_related = (
        "card",
        "card__company",
        "station",
    )