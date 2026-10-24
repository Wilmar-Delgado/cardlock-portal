from django import forms

from companies.models import Company

from .models import FuelCard


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