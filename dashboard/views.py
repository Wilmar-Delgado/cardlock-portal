from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from cards.models import FuelCard
from companies.access import get_user_company
from companies.models import Company, Employee
from stations.models import CardLockStation
from transactions.models import FuelTransaction


@login_required
def index(request):
    company = get_user_company(request.user)

    if company is None:
        companies = Company.objects.all()
        employees = Employee.objects.all()
        cards = FuelCard.objects.all()
        transactions = FuelTransaction.objects.all()
    else:
        companies = Company.objects.filter(id=company.id)

        employees = Employee.objects.filter(
            company=company,
        )

        cards = FuelCard.objects.filter(
            company=company,
        )

        transactions = FuelTransaction.objects.filter(
            card__company=company,
        )

    total_spend = (
        transactions.aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    total_litres = (
        transactions.aggregate(
            total=Sum("litres")
        )["total"]
        or 0
    )

    stats = {
        "companies": companies.count(),
        "employees": employees.count(),
        "active_cards": cards.filter(
            status=FuelCard.Status.ACTIVE
        ).count(),
        "stations": CardLockStation.objects.filter(
            is_active=True
        ).count(),
        "total_spend": total_spend,
        "total_litres": total_litres,
    }

    recent_transactions = (
        transactions
        .select_related(
            "card",
            "card__company",
            "station",
        )
        .order_by("-transaction_at")[:10]
    )

    return render(
        request,
        "dashboard/index.html",
        {
            "stats": stats,
            "recent_transactions": recent_transactions,
            "company": company,
        },
    )