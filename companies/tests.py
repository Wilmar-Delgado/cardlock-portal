from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Company, CompanyMembership, Employee


class EmployeeAccessTests(TestCase):
    def setUp(self):
        self.company_a = Company.objects.create(
            name="Company A",
            account_number="EMP-TEST-A",
        )

        self.company_b = Company.objects.create(
            name="Company B",
            account_number="EMP-TEST-B",
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

        self.employee_a = Employee.objects.create(
            company=self.company_a,
            employee_number="A-001",
            first_name="Alice",
            last_name="Driver",
        )

        self.employee_b = Employee.objects.create(
            company=self.company_b,
            employee_number="B-001",
            first_name="Bob",
            last_name="Driver",
        )

        self.client.login(
            username="manager_a",
            password="test-password-123",
        )

    def test_user_can_view_employee_from_own_company(self):
        response = self.client.get(
            reverse(
                "companies:employee_detail",
                args=[self.employee_a.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_cannot_view_employee_from_another_company(self):
        response = self.client.get(
            reverse(
                "companies:employee_detail",
                args=[self.employee_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )


class EmployeePermissionTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(
            name="Test Transport",
            account_number="EMP-TRANSPORT",
        )

        self.other_company = Company.objects.create(
            name="Other Transport",
            account_number="EMP-OTHER",
        )

        self.manager = User.objects.create_user(
            username="employee_manager",
            password="test-password-123",
        )

        self.viewer = User.objects.create_user(
            username="employee_viewer",
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

        self.employee = Employee.objects.create(
            company=self.company,
            employee_number="E-001",
            first_name="Michael",
            last_name="Brown",
            job_title="Driver",
        )

    def test_manager_can_access_create_employee_page(self):
        self.client.login(
            username="employee_manager",
            password="test-password-123",
        )

        response = self.client.get(
            reverse("companies:employee_create")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_viewer_cannot_access_create_employee_page(self):
        self.client.login(
            username="employee_viewer",
            password="test-password-123",
        )

        response = self.client.get(
            reverse("companies:employee_create")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_can_access_edit_employee_page(self):
        self.client.login(
            username="employee_manager",
            password="test-password-123",
        )

        response = self.client.get(
            reverse(
                "companies:employee_edit",
                args=[self.employee.id],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_viewer_cannot_access_edit_employee_page(self):
        self.client.login(
            username="employee_viewer",
            password="test-password-123",
        )

        response = self.client.get(
            reverse(
                "companies:employee_edit",
                args=[self.employee.id],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_manager_cannot_create_employee_for_another_company(self):
        self.client.login(
            username="employee_manager",
            password="test-password-123",
        )

        response = self.client.post(
            reverse("companies:employee_create"),
            data={
                "company": self.other_company.id,
                "employee_number": "E-999",
                "first_name": "Tampered",
                "last_name": "Employee",
                "email": "tampered@example.com",
                "phone": "",
                "job_title": "Driver",
                "is_active": True,
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        employee = Employee.objects.get(
            employee_number="E-999"
        )

        self.assertEqual(
            employee.company,
            self.company,
        )

        self.assertNotEqual(
            employee.company,
            self.other_company,
        )


class EmployeeMembershipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="employee_no_membership",
            password="test-password-123",
        )

        self.client.login(
            username="employee_no_membership",
            password="test-password-123",
        )

    def test_user_without_company_membership_gets_forbidden(self):
        response = self.client.get(
            reverse("companies:employee_list")
        )

        self.assertEqual(
            response.status_code,
            403,
        )