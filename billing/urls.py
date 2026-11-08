from django.urls import path

from . import views


app_name = "billing"

urlpatterns = [
    path(
        "",
        views.invoice_list,
        name="invoice_list",
    ),
    path(
        "<int:pk>/",
        views.invoice_detail,
        name="invoice_detail",
    ),
    path(
        "<int:pk>/pay/",
        views.create_checkout_session,
        name="create_checkout_session",
    ),
    path(
        "<int:pk>/success/",
        views.payment_success,
        name="payment_success",
    ),
    path(
        "stripe/webhook/",
        views.stripe_webhook,
        name="stripe_webhook",
    ),
]