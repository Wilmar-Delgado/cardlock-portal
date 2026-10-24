from django.contrib import admin

from .models import Company, CompanyMembership, Employee


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account_number",
        "contact_name",
        "is_active",
        "created_at",
    )
    search_fields = (
        "name",
        "account_number",
        "contact_name",
        "contact_email",
    )
    list_filter = ("is_active",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_number",
        "first_name",
        "last_name",
        "company",
        "job_title",
        "is_active",
    )
    search_fields = (
        "employee_number",
        "first_name",
        "last_name",
        "email",
        "company__name",
    )
    list_filter = (
        "is_active",
        "job_title",
    )
    list_select_related = ("company",)


@admin.register(CompanyMembership)
class CompanyMembershipAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "company",
        "role",
        "is_active",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "company__name",
    )

    list_filter = (
        "role",
        "is_active",
    )

    list_select_related = (
        "user",
        "company",
    )