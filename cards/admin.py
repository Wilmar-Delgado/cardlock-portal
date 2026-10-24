from django.contrib import admin

from .models import CardAssignment, FuelCard


@admin.register(FuelCard)
class FuelCardAdmin(admin.ModelAdmin):
    list_display = (
        "card_number",
        "company",
        "network",
        "status",
        "issued_at",
        "expires_at",
    )
    search_fields = (
        "card_number",
        "company__name",
        "network",
    )
    list_filter = (
        "status",
        "network",
    )
    list_select_related = ("company",)


@admin.register(CardAssignment)
class CardAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "card",
        "employee",
        "assigned_at",
        "unassigned_at",
    )
    search_fields = (
        "card__card_number",
        "employee__first_name",
        "employee__last_name",
    )
    list_select_related = (
        "card",
        "employee",
    )