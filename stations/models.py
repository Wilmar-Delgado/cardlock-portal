from django.db import models


class FuelType(models.TextChoices):
    DIESEL = "diesel", "Diesel"
    REGULAR = "regular", "Regular"
    PREMIUM = "premium", "Premium"


class CardLockStation(models.Model):
    station_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    network = models.CharField(max_length=100, blank=True)

    address_line_1 = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default="Canada")

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.station_code})"


class FuelPrice(models.Model):
    station = models.ForeignKey(
        CardLockStation,
        on_delete=models.PROTECT,
        related_name="fuel_prices",
    )
    fuel_type = models.CharField(
        max_length=20,
        choices=FuelType.choices,
    )
    price_per_litre = models.DecimalField(
        max_digits=6,
        decimal_places=3,
    )
    effective_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["station", "fuel_type", "effective_at"],
                name="unique_station_fuel_price_effective_at",
            )
        ]

    def __str__(self):
        return (
            f"{self.station.name} - "
            f"{self.get_fuel_type_display()} - "
            f"${self.price_per_litre}/L"
        )