from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "",
        include("dashboard.urls"),
    ),

    path(
        "accounts/",
        include("django.contrib.auth.urls"),
    ),

    path(
        "cards/",
        include("cards.urls"),
    ),

    path(
        "employees/",
        include("companies.urls"),
    ),
]