from django import forms

from companies.models import Company

from .models import CardAssignment, FuelCard


class FuelCardForm(forms.ModelForm):
    class Meta:
        model = FuelCard

        fields = [
            "company",
            "card_number",
            "network",
            "status",
            "issued_at",
            "expires_at",
        ]

        widgets = {
            "issued_at": forms.DateInput(
                attrs={"type": "date"}
            ),
            "expires_at": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

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

        issued_at = cleaned_data.get("issued_at")
        expires_at = cleaned_data.get("expires_at")

        if (
            issued_at
            and expires_at
            and expires_at < issued_at
        ):
            self.add_error(
                "expires_at",
                "Expiration date cannot be before the issue date.",
            )

        return cleaned_data


class CardAssignmentForm(forms.ModelForm):
    class Meta:
        model = CardAssignment

        fields = [
            "card",
            "assigned_at",
        ]

        widgets = {
            "assigned_at": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(
        self,
        *args,
        employee=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.employee = employee

        if employee:
            active_assignments = CardAssignment.objects.filter(
                unassigned_at__isnull=True
            )

            self.fields["card"].queryset = (
                FuelCard.objects
                .filter(
                    company=employee.company,
                    status=FuelCard.Status.ACTIVE,
                )
                .exclude(
                    assignments__in=active_assignments
                )
                .order_by("card_number")
            )

    def clean_card(self):
        card = self.cleaned_data["card"]

        if card.company_id != self.employee.company_id:
            raise forms.ValidationError(
                "This card belongs to another company."
            )

        if card.assignments.filter(
            unassigned_at__isnull=True
        ).exists():
            raise forms.ValidationError(
                "This card is already assigned."
            )

        return card