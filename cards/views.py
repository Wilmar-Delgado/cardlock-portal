from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from companies.access import (
    can_manage_company_data,
    get_user_company,
    require_manage_permission,
)

from .forms import FuelCardForm
from .models import FuelCard

def get_accessible_cards(user):
    company = get_user_company(user)

    cards = FuelCard.objects.select_related(
        "company",
    )

    if company is not None:
        cards = cards.filter(
            company=company,
        )

    return cards, company


@login_required
def list_cards(request):
    cards, company = get_accessible_cards(
        request.user
    )

    search = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        cards = cards.filter(
            Q(card_number__icontains=search)
            | Q(network__icontains=search)
            | Q(company__name__icontains=search)
        )

    if status in FuelCard.Status.values:
        cards = cards.filter(
            status=status,
        )

    cards = cards.order_by(
        "company__name",
        "card_number",
    )

    return render(
        request,
        "cards/list.html",
        {
            "cards": cards,
            "company": company,
            "search": search,
            "status": status,
            "statuses": FuelCard.Status.choices,
            "can_manage_cards": can_manage_company_data(
                request.user
            ),
        },
    )


@login_required
def card_detail(request, pk):
    cards, company = get_accessible_cards(
        request.user
    )

    card = get_object_or_404(
        cards,
        pk=pk,
    )

    assignments = (
        card.assignments
        .select_related(
            "employee",
        )
        .order_by("-assigned_at")
    )

    return render(
        request,
        "cards/detail.html",
        {
            "card": card,
            "company": company,
            "assignments": assignments,
            "can_manage_cards": can_manage_company_data(
                request.user
            ),
        },
    )


@login_required
def create_card(request):
    require_manage_permission(request.user)

    company = get_user_company(request.user)

    form = FuelCardForm(
        request.POST or None,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        card = form.save(commit=False)

        if company is not None:
            card.company = company

        card.save()

        return redirect(
            "cards:detail",
            pk=card.pk,
        )

    return render(
        request,
        "cards/form.html",
        {
            "form": form,
            "title": "Add Fuel Card",
            "company": company,
        },
    )


@login_required
def edit_card(request, pk):
    require_manage_permission(request.user)

    cards, company = get_accessible_cards(
        request.user
    )

    card = get_object_or_404(
        cards,
        pk=pk,
    )

    form = FuelCardForm(
        request.POST or None,
        instance=card,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        card = form.save(commit=False)

        if company is not None:
            card.company = company

        card.save()

        return redirect(
            "cards:detail",
            pk=card.pk,
        )

    return render(
        request,
        "cards/form.html",
        {
            "form": form,
            "title": "Edit Fuel Card",
            "company": company,
            "card": card,
        },
    )