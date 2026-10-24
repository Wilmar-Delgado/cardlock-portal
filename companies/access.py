from django.core.exceptions import PermissionDenied

from .models import CompanyMembership


def get_user_company(user):
    if user.is_superuser:
        return None

    try:
        membership = user.company_membership
    except CompanyMembership.DoesNotExist:
        raise PermissionDenied(
            "Your account is not assigned to a company."
        )

    if not membership.is_active:
        raise PermissionDenied(
            "Your company membership is inactive."
        )

    return membership.company


def can_manage_company_data(user):
    if user.is_superuser:
        return True

    try:
        membership = user.company_membership
    except CompanyMembership.DoesNotExist:
        return False

    if not membership.is_active:
        return False

    return membership.role in {
        CompanyMembership.Role.ADMIN,
        CompanyMembership.Role.MANAGER,
    }


def require_manage_permission(user):
    if not can_manage_company_data(user):
        raise PermissionDenied(
            "You do not have permission to modify this data."
        )