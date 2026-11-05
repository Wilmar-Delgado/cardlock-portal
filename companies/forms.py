from django import forms

from .models import Company, Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee

        fields = [
            "company",
            "employee_number",
            "first_name",
            "last_name",
            "email",
            "phone",
            "job_title",
            "is_active",
        ]

    def __init__(
        self,
        *args,
        user=None,
        company=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.user = user
        self.company = company

        if user and user.is_superuser:
            self.fields["company"].queryset = (
                Company.objects
                .filter(is_active=True)
                .order_by("name")
            )
        else:
            self.fields.pop("company")

    def clean(self):
        cleaned_data = super().clean()

        employee_number = cleaned_data.get(
            "employee_number"
        )

        if self.user and self.user.is_superuser:
            company = cleaned_data.get("company")
        else:
            company = self.company

        if company and employee_number:
            existing_employee = (
                Employee.objects
                .filter(
                    company=company,
                    employee_number=employee_number,
                )
                .exclude(pk=self.instance.pk)
            )

            if existing_employee.exists():
                self.add_error(
                    "employee_number",
                    "This employee number already exists "
                    "for this company.",
                )

        return cleaned_data