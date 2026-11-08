from django.db import models

from companies.models import Company


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        VOID = "void", "Void"

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
    )

    period_start = models.DateField()
    period_end = models.DateField()

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} - {self.company.name}"