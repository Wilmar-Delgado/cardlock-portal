import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from cards.models import CardAssignment, FuelCard
from companies.models import Company, Employee
from stations.models import CardLockStation, FuelPrice, FuelType
from transactions.models import FuelTransaction


class Command(BaseCommand):
    help = "Seed realistic demo data for the Card-Lock Portal"

    def handle(self, *args, **options):
        fake = Faker("en_CA")

        Faker.seed(2026)
        random.seed(2026)

        self.stdout.write("Seeding demo data...")

        companies = self.seed_companies(fake)
        stations = self.seed_stations()

        for company_index, company in enumerate(companies, start=1):
            employees = self.seed_employees(
                fake,
                company,
                company_index,
            )

            cards = self.seed_cards(
                company,
                employees,
                company_index,
            )

            self.seed_transactions(
                cards,
                stations,
                company_index,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Demo data seeded successfully."
            )
        )

    def seed_companies(self, fake):
        companies = []

        for index in range(1, 6):
            company, _ = Company.objects.update_or_create(
                account_number=f"DEMO-{index:04d}",
                defaults={
                    "name": fake.company(),
                    "contact_name": fake.name(),
                    "contact_email": fake.company_email(),
                    "phone": fake.phone_number()[:30],
                    "is_active": True,
                },
            )

            companies.append(company)

        return companies

    def seed_employees(self, fake, company, company_index):
        employees = []

        job_titles = [
            "Driver",
            "Driver",
            "Operations Manager",
            "Fleet Supervisor",
            "Dispatcher",
        ]

        for index in range(1, 6):
            employee, _ = Employee.objects.update_or_create(
                company=company,
                employee_number=f"E{index:03d}",
                defaults={
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "email": fake.email(),
                    "phone": fake.phone_number()[:30],
                    "job_title": job_titles[index - 1],
                    "is_active": True,
                },
            )

            employees.append(employee)

        return employees

    def seed_cards(self, company, employees, company_index):
        cards = []

        networks = [
            "Petro-Pass",
            "Esso Commercial Cardlock",
            "Shell Cardlock",
        ]

        for index in range(1, 4):
            card, _ = FuelCard.objects.update_or_create(
                card_number=f"DEMO-{company_index:02d}-{index:04d}",
                defaults={
                    "company": company,
                    "network": networks[index - 1],
                    "status": FuelCard.Status.ACTIVE,
                    "issued_at": timezone.localdate()
                    - timedelta(days=180 + index * 15),
                    "expires_at": timezone.localdate()
                    + timedelta(days=365),
                },
            )

            employee = employees[index - 1]

            CardAssignment.objects.get_or_create(
                card=card,
                employee=employee,
                assigned_at=timezone.localdate()
                - timedelta(days=90),
                defaults={
                    "unassigned_at": None,
                },
            )

            cards.append(card)

        return cards

    def seed_stations(self):
        station_data = [
            {
                "station_code": "DEMO-CGY-NE",
                "name": "Calgary Northeast Cardlock",
                "network": "Petro-Pass",
                "address_line_1": "1234 32 Ave NE",
                "city": "Calgary",
                "province": "Alberta",
                "postal_code": "T2E 6T4",
                "latitude": Decimal("51.081000"),
                "longitude": Decimal("-114.020000"),
            },
            {
                "station_code": "DEMO-AIR-01",
                "name": "Airdrie Cardlock",
                "network": "Shell Cardlock",
                "address_line_1": "100 Gateway Dr NE",
                "city": "Airdrie",
                "province": "Alberta",
                "postal_code": "T4B 0J6",
                "latitude": Decimal("51.291700"),
                "longitude": Decimal("-114.014400"),
            },
            {
                "station_code": "DEMO-RD-01",
                "name": "Red Deer Cardlock",
                "network": "Esso Commercial Cardlock",
                "address_line_1": "5000 67 St",
                "city": "Red Deer",
                "province": "Alberta",
                "postal_code": "T4N 7A1",
                "latitude": Decimal("52.269000"),
                "longitude": Decimal("-113.811600"),
            },
            {
                "station_code": "DEMO-EDM-S",
                "name": "Edmonton South Cardlock",
                "network": "Petro-Pass",
                "address_line_1": "7400 51 Ave NW",
                "city": "Edmonton",
                "province": "Alberta",
                "postal_code": "T6B 2W2",
                "latitude": Decimal("53.488000"),
                "longitude": Decimal("-113.441000"),
            },
        ]

        stations = []
        effective_at = timezone.now().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        fuel_prices = {
            FuelType.DIESEL: Decimal("1.469"),
            FuelType.REGULAR: Decimal("1.389"),
            FuelType.PREMIUM: Decimal("1.579"),
        }

        for station_values in station_data:
            station_code = station_values["station_code"]

            defaults = {
                key: value
                for key, value in station_values.items()
                if key != "station_code"
            }

            station, _ = CardLockStation.objects.update_or_create(
                station_code=station_code,
                defaults=defaults,
            )

            for fuel_type, base_price in fuel_prices.items():
                variation = Decimal(
                    str(random.choice(["-0.020", "-0.010", "0", "0.010", "0.020"]))
                )

                FuelPrice.objects.update_or_create(
                    station=station,
                    fuel_type=fuel_type,
                    effective_at=effective_at,
                    defaults={
                        "price_per_litre": base_price + variation,
                    },
                )

            stations.append(station)

        return stations

    def seed_transactions(
        self,
        cards,
        stations,
        company_index,
    ):
        fuel_types = [
            FuelType.DIESEL,
            FuelType.REGULAR,
        ]

        for card_index, card in enumerate(cards, start=1):
            for transaction_index in range(1, 11):
                station = random.choice(stations)
                fuel_type = random.choice(fuel_types)

                price = (
                    FuelPrice.objects.filter(
                        station=station,
                        fuel_type=fuel_type,
                    )
                    .order_by("-effective_at")
                    .values_list("price_per_litre", flat=True)
                    .first()
                )

                litres = Decimal(
                    str(round(random.uniform(35, 120), 3))
                )

                total = (
                    litres * price
                ).quantize(Decimal("0.01"))

                FuelTransaction.objects.update_or_create(
                    external_reference=(
                        f"DEMO-TXN-"
                        f"{company_index:02d}-"
                        f"{card_index:02d}-"
                        f"{transaction_index:03d}"
                    ),
                    defaults={
                        "card": card,
                        "station": station,
                        "fuel_type": fuel_type,
                        "litres": litres,
                        "price_per_litre": price,
                        "total_amount": total,
                        "transaction_at": (
                            timezone.now()
                            - timedelta(
                                days=random.randint(0, 60),
                                hours=random.randint(0, 23),
                            )
                        ),
                    },
                )