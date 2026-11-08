from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from companies.models import Company, CompanyMembership

from .models import Invoice


User = get_user_model()


class FakeStripeSession:
    """
    Small fake object that behaves like the Stripe Session object
    our webhook receives.

    Our view calls:
        event["data"]["object"].to_dict()
    """

    def __init__(self, data):
        self.data = data

    def to_dict(self):
        return self.data


class BillingTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Dixon-Mckenzie",
            account_number="TEST-1001",
        )

        self.other_company = Company.objects.create(
            name="Other Transport Ltd.",
            account_number="TEST-2001",
        )

        self.user = User.objects.create_user(
            username="billing_manager",
            password="test-password-123",
        )

        CompanyMembership.objects.create(
            user=self.user,
            company=self.company,
            role=CompanyMembership.Role.MANAGER,
        )

        self.invoice = self.create_invoice(
            company=self.company,
            invoice_number="INV-TEST-001",
        )

        self.other_invoice = self.create_invoice(
            company=self.other_company,
            invoice_number="INV-OTHER-001",
        )

        self.client.force_login(self.user)

    def create_invoice(
        self,
        company,
        invoice_number,
        status=Invoice.Status.OPEN,
    ):
        return Invoice.objects.create(
            company=company,
            invoice_number=invoice_number,
            period_start=date(2026, 10, 1),
            period_end=date(2026, 10, 31),
            subtotal=Decimal("100.00"),
            tax=Decimal("5.00"),
            total=Decimal("105.00"),
            due_date=date(2026, 11, 30),
            status=status,
        )

    def create_paid_webhook_event(self):
        return {
            "type": "checkout.session.completed",
            "data": {
                "object": FakeStripeSession(
                    {
                        "id": "cs_test_123",
                        "payment_status": "paid",
                        "payment_intent": "pi_test_123",
                        "metadata": {
                            "invoice_id": str(
                                self.invoice.id
                            ),
                            "invoice_number":
                                self.invoice.invoice_number,
                        },
                    }
                )
            },
        }

    def test_user_can_view_own_company_invoice(self):
        response = self.client.get(
            reverse(
                "billing:invoice_detail",
                args=[self.invoice.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_cannot_view_other_company_invoice(self):
        response = self.client.get(
            reverse(
                "billing:invoice_detail",
                args=[self.other_invoice.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_unit_test"
    )
    @patch("billing.views.stripe.StripeClient")
    def test_open_invoice_creates_checkout_session(
        self,
        mock_stripe_client,
    ):
        checkout_session = SimpleNamespace(
            id="cs_test_123",
            url=(
                "https://checkout.stripe.com/"
                "c/pay/cs_test_123"
            ),
        )

        stripe_client = (
            mock_stripe_client.return_value
        )

        stripe_client.v1.checkout.sessions.create.return_value = (
            checkout_session
        )

        response = self.client.post(
            reverse(
                "billing:create_checkout_session",
                args=[self.invoice.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response["Location"],
            checkout_session.url,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.stripe_checkout_session_id,
            "cs_test_123",
        )

        create_mock = (
            stripe_client
            .v1
            .checkout
            .sessions
            .create
        )

        create_mock.assert_called_once()

        params = (
            create_mock
            .call_args
            .kwargs["params"]
        )

        self.assertEqual(
            params["mode"],
            "payment",
        )

        self.assertEqual(
            params["line_items"][0]
            ["price_data"]
            ["currency"],
            "cad",
        )

        self.assertEqual(
            params["line_items"][0]
            ["price_data"]
            ["unit_amount"],
            10500,
        )

        self.assertEqual(
            params["metadata"]["invoice_id"],
            str(self.invoice.id),
        )

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_unit_test"
    )
    @patch("billing.views.stripe.StripeClient")
    def test_non_open_invoice_cannot_start_checkout(
        self,
        mock_stripe_client,
    ):
        self.invoice.status = Invoice.Status.PAID
        self.invoice.save()

        response = self.client.post(
            reverse(
                "billing:create_checkout_session",
                args=[self.invoice.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        mock_stripe_client.assert_not_called()

    def test_success_page_does_not_mark_invoice_paid(self):
        response = self.client.get(
            reverse(
                "billing:payment_success",
                args=[self.invoice.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            Invoice.Status.OPEN,
        )

        self.assertIsNone(
            self.invoice.paid_at,
        )

    @override_settings(
        STRIPE_WEBHOOK_SECRET="whsec_test_secret"
    )
    def test_invalid_webhook_signature_returns_400(self):
        response = self.client.post(
            reverse(
                "billing:stripe_webhook"
            ),
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid-signature",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    @patch(
        "billing.views.stripe.Webhook.construct_event"
    )
    def test_paid_webhook_marks_invoice_paid(
        self,
        mock_construct_event,
    ):
        self.invoice.stripe_checkout_session_id = (
            "cs_test_123"
        )

        self.invoice.save()

        mock_construct_event.return_value = (
            self.create_paid_webhook_event()
        )

        response = self.client.post(
            reverse(
                "billing:stripe_webhook"
            ),
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.status,
            Invoice.Status.PAID,
        )

        self.assertIsNotNone(
            self.invoice.paid_at,
        )

        self.assertEqual(
            self.invoice.stripe_checkout_session_id,
            "cs_test_123",
        )

        self.assertEqual(
            self.invoice.stripe_payment_intent_id,
            "pi_test_123",
        )

    @patch(
        "billing.views.stripe.Webhook.construct_event"
    )
    def test_paid_webhook_is_idempotent(
        self,
        mock_construct_event,
    ):
        self.invoice.stripe_checkout_session_id = (
            "cs_test_123"
        )

        self.invoice.save()

        mock_construct_event.return_value = (
            self.create_paid_webhook_event()
        )

        webhook_url = reverse(
            "billing:stripe_webhook"
        )

        first_response = self.client.post(
            webhook_url,
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )

        self.invoice.refresh_from_db()

        first_paid_at = self.invoice.paid_at

        second_response = self.client.post(
            webhook_url,
            data="{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )

        self.invoice.refresh_from_db()

        self.assertEqual(
            first_response.status_code,
            200,
        )

        self.assertEqual(
            second_response.status_code,
            200,
        )

        self.assertEqual(
            self.invoice.status,
            Invoice.Status.PAID,
        )

        self.assertEqual(
            self.invoice.paid_at,
            first_paid_at,
        )