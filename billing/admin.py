from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "company",
        "period_start",
        "period_end",
        "total",
        "due_date",
        "status",
        "paid_at",
    )

    search_fields = (
        "invoice_number",
        "company__name",
        "stripe_checkout_session_id",
        "stripe_payment_intent_id",
    )

    list_filter = (
        "status",
        "due_date",
    )

    list_select_related = (
        "company",
    )