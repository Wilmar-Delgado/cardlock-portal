from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from companies.models import Company, CompanyMembership

from .models import FuelCard


class FuelCardAccessTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(
            name="Company A",
            account_number="TEST-A",
        )

        self.company_b = Company.objects.create(
            name="Company B",
            account_number="TEST-B",
        )

        self.user = User.objects.create_user(
            username="manager_a",
            password="test-password-123",
        )

        CompanyMembership.objects.create(
            user=self.user,
            company=self.company_a,
            role=CompanyMembership.Role.MANAGER,
        )

        self.card_a = FuelCard.objects.create(
            company=self.company_a,
            card_number="CARD-A-001",
            network="Petro-Pass",
        )

        self.card_b = FuelCard.objects.create(
            company=self.company_b,
            card_number="CARD-B-001",
            network="Petro-Pass",
        )

        self.client.login(
            username="manager_a",
            password="test-password-123",
        )

    def test_user_can_view_card_from_own_company(self):
        response = self.client.get(
            reverse(
                "cards:detail",
                args=[self.card_a.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_cannot_view_card_from_another_company(self):
        response = self.client.get(
            reverse(
                "cards:detail",
                args=[self.card_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class FuelCardPermissionTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Transport",
            account_number="TEST-TRANSPORT",
        )

        self.other_company = Company.objects.create(
            name="Other Transport",
            account_number="OTHER-TRANSPORT",
        )

        self.manager = User.objects.create_user(
            username="manager",
            password="test-password-123",
        )

        self.viewer = User.objects.create_user(
            username="viewer",
            password="test-password-123",
        )

        CompanyMembership.objects.create(
            user=self.manager,
            company=self.company,
            role=CompanyMembership.Role.MANAGER,
        )

        CompanyMembership.objects.create(
            user=self.viewer,
            company=self.company,
            role=CompanyMembership.Role.VIEWER,
        )

        self.card = FuelCard.objects.create(
            company=self.company,
            card_number="TEST-CARD-001",
            network="Petro-Pass",
        )

    def test_manager_can_access_create_card_page(self):
        self.client.login(
            username="manager",
            password="test-password-123",
        )

        response = self.client.get(
            reverse("cards:create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_viewer_cannot_access_create_card_page(self):
        self.client.login(
            username="viewer",
            password="test-password-123",
        )

        response = self.client.get(
            reverse("cards:create")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_can_access_edit_card_page(self):
        self.client.login(
            username="manager",
            password="test-password-123",
        )

        response = self.client.get(
            reverse(
                "cards:edit",
                args=[self.card.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_viewer_cannot_access_edit_card_page(self):
        self.client.login(
            username="viewer",
            password="test-password-123",
        )

        response = self.client.get(
            reverse(
                "cards:edit",
                args=[self.card.id],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_cannot_create_card_for_another_company(self):
        self.client.login(
            username="manager",
            password="test-password-123",
        )

        response = self.client.post(
            reverse("cards:create"),
            data={
                "company": self.other_company.id,
                "card_number": "MANAGER-CARD-001",
                "network": "Petro-Pass",
                "status": FuelCard.Status.ACTIVE,
                "issued_at": "",
                "expires_at": "",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        card = FuelCard.objects.get(
            card_number="MANAGER-CARD-001"
        )

        self.assertEqual(
            card.company,
            self.company,
        )

        self.assertNotEqual(
            card.company,
            self.other_company,
        )

class FuelCardMembershipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="no_membership_user",
            password="test-password-123",
        )

        self.client.login(
            username="no_membership_user",
            password="test-password-123",
        )

    def test_user_without_company_membership_gets_forbidden(self):
        response = self.client.get(
            reverse("cards:list")
        )

        self.assertEqual(
            response.status_code,
            403,
        )
