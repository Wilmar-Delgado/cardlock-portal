from django.urls import path

from . import views


app_name = "cards"

urlpatterns = [
    path(
        "",
        views.list_cards,
        name="list",
    ),
    path(
        "create/",
        views.create_card,
        name="create",
    ),
    path(
        "<int:pk>/",
        views.card_detail,
        name="detail",
    ),
    path(
        "<int:pk>/edit/",
        views.edit_card,
        name="edit",
    ),
]