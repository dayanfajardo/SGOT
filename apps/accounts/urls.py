from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import RedirectView

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "users/",
        views.user_list,
        name="user_list",
    ),
    path(
        "users/new/",
        views.user_create,
        name="user_create",
    ),
    path(
        "users/<int:pk>/edit/",
        views.user_update,
        name="user_update",
    ),
    path(
        "users/<int:pk>/toggle-active/",
        views.user_toggle_active,
        name="user_toggle_active",
    ),
    path(
        "users/<int:pk>/reset-password/",
        views.user_reset_password,
        name="user_reset_password",
    ),
    path(
        "users/<int:pk>/",
        views.user_detail,
        name="user_detail",
    ),
    path(
        "",
        login_required(
            RedirectView.as_view(pattern_name="workorders:dashboard")
        ),
        name="home",
    ),
]
