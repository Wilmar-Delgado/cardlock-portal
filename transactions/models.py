from django.db import models

from cards.models import FuelCard
from stations.models import CardLockStation, FuelType


class FuelTransaction(models.Model):
    card = models.ForeignKey(
        FuelCard,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    station = models.ForeignKey(
        CardLockStation,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    fuel_type = models.CharField(
        max_length=20,
        choices=FuelType.choices,
    )

    litres = models.DecimalField(
        max_digits=10,
        decimal_places=3,
    )
    price_per_litre = models.DecimalField(
        max_digits=6,
        decimal_places=3,
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    transaction_at = models.DateTimeField()

    external_reference = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-transaction_at"]
        indexes = [
            models.Index(fields=["card", "transaction_at"]),
            models.Index(fields=["station", "transaction_at"]),
        ]

    def __str__(self):
        return (
            f"{self.card.card_number} - "
            f"{self.station.name} - "
            f"${self.total_amount}"
        )