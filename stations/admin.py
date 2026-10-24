from django.contrib import admin

from .models import CardLockStation, FuelPrice


@admin.register(CardLockStation)
class CardLockStationAdmin(admin.ModelAdmin):
    list_display = (
        "station_code",
        "name",
        "network",
        "city",
        "province",
        "is_active",
    )
    search_fields = (
        "station_code",
        "name",
        "city",
        "province",
    )
    list_filter = (
        "network",
        "province",
        "is_active",
    )


@admin.register(FuelPrice)
class FuelPriceAdmin(admin.ModelAdmin):
    list_display = (
        "station",
        "fuel_type",
        "price_per_litre",
        "effective_at",
    )
    list_filter = ("fuel_type",)
    list_select_related = ("station",)