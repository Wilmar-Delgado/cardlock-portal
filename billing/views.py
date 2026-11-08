from decimal import Decimal

import stripe
from stripe import SignatureVerificationError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from companies.access import get_user_company

from .models import Invoice


def get_accessible_invoices(user):
    company = get_user_company(user)

    invoices = Invoice.objects.select_related(
        "company"
    )

    if company is not None:
        invoices = invoices.filter(
            company=company
        )

    return invoices, company


@login_required
def invoice_list(request):
    invoices, company = get_accessible_invoices(
        request.user
    )

    invoices = invoices.order_by(
        "-created_at"
    )

    return render(
        request,
        "billing/invoices/list.html",
        {
            "invoices": invoices,
            "company": company,
        },
    )


@login_required
def invoice_detail(request, pk):
    invoices, company = get_accessible_invoices(
        request.user
    )

    invoice = get_object_or_404(
        invoices,
        pk=pk,
    )

    return render(
        request,
        "billing/invoices/detail.html",
        {
            "invoice": invoice,
            "company": company,
        },
    )


@login_required
@require_POST
def create_checkout_session(request, pk):
    invoices, company = get_accessible_invoices(
        request.user
    )

    invoice = get_object_or_404(
        invoices,
        pk=pk,
    )

    if invoice.status != Invoice.Status.OPEN:
        return HttpResponseBadRequest(
            "Only open invoices can be paid."
        )

    stripe_client = stripe.StripeClient(
        settings.STRIPE_SECRET_KEY
    )

    success_url = (
        request.build_absolute_uri(
            reverse(
                "billing:payment_success",
                args=[invoice.pk],
            )
        )
        + "?session_id={CHECKOUT_SESSION_ID}"
    )

    cancel_url = request.build_absolute_uri(
        reverse(
            "billing:invoice_detail",
            args=[invoice.pk],
        )
    )

    amount_in_cents = int(
        invoice.total * Decimal("100")
    )

    checkout_session = (
        stripe_client.v1.checkout.sessions.create(
            params={
                "mode": "payment",

                "line_items": [
                    {
                        "price_data": {
                            "currency": "cad",
                            "product_data": {
                                "name": (
                                    f"Invoice "
                                    f"{invoice.invoice_number}"
                                ),
                            },
                            "unit_amount": amount_in_cents,
                        },
                        "quantity": 1,
                    }
                ],

                "metadata": {
                    "invoice_id": str(invoice.id),
                    "invoice_number":
                        invoice.invoice_number,
                },

                "success_url": success_url,
                "cancel_url": cancel_url,
            }
        )
    )

    invoice.stripe_checkout_session_id = (
        checkout_session.id
    )

    invoice.save()

    return redirect(
        checkout_session.url
    )


@login_required
def payment_success(request, pk):
    invoices, company = get_accessible_invoices(
        request.user
    )

    invoice = get_object_or_404(
        invoices,
        pk=pk,
    )

    return render(
        request,
        "billing/invoices/success.html",
        {
            "invoice": invoice,
            "company": company,
        },
    )


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE"
    )

    if not signature:
        return HttpResponseBadRequest(
            "Missing Stripe signature."
        )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )

    except ValueError:
        return HttpResponseBadRequest(
            "Invalid webhook payload."
        )

    except SignatureVerificationError:
        return HttpResponseBadRequest(
            "Invalid webhook signature."
        )

    if event["type"] in {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }:
        session = event["data"]["object"].to_dict()

        if session.get("payment_status") == "paid":
            invoice_id = (
                session
                .get("metadata", {})
                .get("invoice_id")
            )

            if invoice_id:
                try:
                    invoice = Invoice.objects.get(
                        pk=invoice_id
                    )
                except Invoice.DoesNotExist:
                    return HttpResponse(
                        status=200
                    )

                if (
                    invoice.stripe_checkout_session_id
                    and
                    invoice.stripe_checkout_session_id
                    != session["id"]
                ):
                    return HttpResponseBadRequest(
                        "Checkout session mismatch."
                    )

                if invoice.status != Invoice.Status.PAID:
                    invoice.status = Invoice.Status.PAID
                    invoice.paid_at = timezone.now()

                    invoice.stripe_checkout_session_id = (
                        session["id"]
                    )

                    invoice.stripe_payment_intent_id = (
                        session.get("payment_intent")
                    )

                    invoice.save(
                        update_fields=[
                            "status",
                            "paid_at",
                            "stripe_checkout_session_id",
                            "stripe_payment_intent_id",
                            "updated_at",
                        ]
                    )

    return HttpResponse(status=200)