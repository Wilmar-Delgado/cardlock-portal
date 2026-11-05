from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from cards.forms import CardAssignmentForm

from .access import (
    can_manage_company_data,
    get_user_company,
    require_manage_permission,
)

from .forms import EmployeeForm
from .models import Employee


def get_accessible_employees(user):
    company = get_user_company(user)

    employees = Employee.objects.select_related(
        "company"
    )

    if company is not None:
        employees = employees.filter(
            company=company
        )

    return employees, company


@login_required
def employee_list(request):
    employees, company = get_accessible_employees(
        request.user
    )

    search = request.GET.get(
        "q",
        "",
    ).strip()

    if search:
        employees = employees.filter(
            Q(employee_number__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
            | Q(job_title__icontains=search)
            | Q(company__name__icontains=search)
        )

    employees = employees.order_by(
        "company__name",
        "last_name",
        "first_name",
    )

    return render(
        request,
        "companies/employees/list.html",
        {
            "employees": employees,
            "company": company,
            "search": search,
            "can_manage_employees":
                can_manage_company_data(
                    request.user
                ),
        },
    )


@login_required
def employee_detail(request, pk):
    employees, company = get_accessible_employees(
        request.user
    )

    employee = get_object_or_404(
        employees,
        pk=pk,
    )

    assignments = (
        employee.card_assignments
        .select_related("card")
        .order_by("-assigned_at")
    )

    return render(
        request,
        "companies/employees/detail.html",
        {
            "employee": employee,
            "company": company,
            "assignments": assignments,
            "can_manage_employees":
                can_manage_company_data(
                    request.user
                ),
        },
    )


@login_required
def employee_create(request):
    require_manage_permission(request.user)

    company = get_user_company(request.user)

    form = EmployeeForm(
        request.POST or None,
        user=request.user,
        company=company,
    )

    if request.method == "POST" and form.is_valid():
        employee = form.save(commit=False)

        if company is not None:
            employee.company = company

        employee.save()

        return redirect(
            "companies:employee_detail",
            pk=employee.pk,
        )

    return render(
        request,
        "companies/employees/form.html",
        {
            "form": form,
            "company": company,
            "title": "Add Employee",
        },
    )


@login_required
def employee_edit(request, pk):
    require_manage_permission(request.user)

    employees, company = get_accessible_employees(
        request.user
    )

    employee = get_object_or_404(
        employees,
        pk=pk,
    )

    form = EmployeeForm(
        request.POST or None,
        instance=employee,
        user=request.user,
        company=company,
    )

    if request.method == "POST" and form.is_valid():
        employee = form.save(commit=False)

        if company is not None:
            employee.company = company

        employee.save()

        return redirect(
            "companies:employee_detail",
            pk=employee.pk,
        )

    return render(
        request,
        "companies/employees/form.html",
        {
            "form": form,
            "employee": employee,
            "company": company,
            "title": "Edit Employee",
        },
    )


@login_required
def assign_card(request, pk):
    require_manage_permission(request.user)

    employees, company = get_accessible_employees(
        request.user
    )

    employee = get_object_or_404(
        employees,
        pk=pk,
    )

    form = CardAssignmentForm(
        request.POST or None,
        employee=employee,
        initial={
            "assigned_at": timezone.localdate(),
        },
    )

    if request.method == "POST" and form.is_valid():
        assignment = form.save(commit=False)

        assignment.employee = employee

        assignment.save()

        return redirect(
            "companies:employee_detail",
            pk=employee.pk,
        )

    return render(
        request,
        "companies/employees/assign_card.html",
        {
            "employee": employee,
            "company": company,
            "form": form,
        },
    )


@login_required
@require_POST
def unassign_card(
    request,
    employee_pk,
    assignment_pk,
):
    require_manage_permission(request.user)

    employees, company = get_accessible_employees(
        request.user
    )

    employee = get_object_or_404(
        employees,
        pk=employee_pk,
    )

    assignment = get_object_or_404(
        employee.card_assignments,
        pk=assignment_pk,
        unassigned_at__isnull=True,
    )

    assignment.unassigned_at = (
        timezone.localdate()
    )

    assignment.save(
        update_fields=["unassigned_at"]
    )

    return redirect(
        "companies:employee_detail",
        pk=employee.pk,
    )