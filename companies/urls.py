from django.urls import path

from . import views


app_name = "companies"

urlpatterns = [
    path(
        "",
        views.employee_list,
        name="employee_list",
    ),
    path(
        "create/",
        views.employee_create,
        name="employee_create",
    ),
    path(
        "<int:pk>/",
        views.employee_detail,
        name="employee_detail",
    ),
    path(
        "<int:pk>/edit/",
        views.employee_edit,
        name="employee_edit",
    ),
    path(
        "<int:pk>/assign-card/",
        views.assign_card,
        name="assign_card",
    ),
    path(
        "<int:employee_pk>/assignments/"
        "<int:assignment_pk>/unassign/",
        views.unassign_card,
        name="unassign_card",
    ),
]